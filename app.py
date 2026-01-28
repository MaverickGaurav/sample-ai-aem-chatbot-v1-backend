"""
Main Flask Application - AEM Compliance Chatbot
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import uuid
import os

from config import Config
from services.ollama_service import OllamaService
from services.aem_service import AEMService
from services.intent_service import IntentService
from services.compliance_service import ComplianceService
from services.export_service import ExportService
from services.file_service import FileService
from services.web_search_service import WebSearchService
from services.langchain_service import LangChainService
from services.vector_service import VectorService

from models.schemas import (
    ChatMode, Intent, ChatRequest, AEMQueryRequest,
    ComplianceCheckRequest, ExportRequest
)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize services
ollama_service = OllamaService()
aem_service = AEMService()
intent_service = IntentService()
compliance_service = ComplianceService()
export_service = ExportService()
file_service = FileService()
web_search_service = WebSearchService()
langchain_service = LangChainService()

# Vector service is optional - may fail if Qdrant not available or model download fails
try:
    vector_service = VectorService()
    print("✓ Vector service initialized")
except Exception as e:
    print(f"⚠ Vector service initialization failed: {e}")
    print("  Continuing without vector/RAG features")
    vector_service = None

Config.init_app(app)


# ==================== CHAT ENDPOINTS ====================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with intent detection and mode routing"""
    try:
        data = request.json
        message = data.get('message', '')
        mode = data.get('mode', ChatMode.CHAT)
        model = data.get('model', Config.DEFAULT_MODEL)
        temperature = data.get('temperature', 0.7)
        conversation_id = data.get('conversation_id') or str(uuid.uuid4())

        # Detect intent
        intent_result = intent_service.detect_intent(message)
        detected_intent = intent_result['intent']
        suggested_mode = intent_result.get('suggested_mode', mode)

        # Auto-switch mode if high confidence
        if intent_result['confidence'] > 0.7 and suggested_mode != mode:
            mode = suggested_mode
            mode_switch_msg = intent_service.get_mode_suggestion_message(mode)
        else:
            mode_switch_msg = None

        # Get conversation context
        context = langchain_service.get_context(conversation_id)

        # Route to appropriate handler based on mode
        if mode == ChatMode.AEM:
            response_msg = _handle_aem_chat(message, intent_result, model)
        elif mode == ChatMode.FILE:
            response_msg = "Please upload a file using the file upload interface."
        elif mode == ChatMode.WEB:
            response_msg = _handle_web_search(message, model)
        else:  # ChatMode.CHAT
            response_msg = _handle_regular_chat(message, context, model, temperature)

        # Add mode switch message if applicable
        if mode_switch_msg:
            response_msg = f"{mode_switch_msg}\n\n{response_msg}"

        # Save to memory
        langchain_service.add_message(conversation_id, message, response_msg)

        return jsonify({
            'message': response_msg,
            'mode': mode,
            'intent': detected_intent,
            'suggested_mode': suggested_mode,
            'conversation_id': conversation_id,
            'metadata': {
                'intent_confidence': intent_result['confidence'],
                'extracted_entities': intent_result.get('extracted_entities', {})
            }
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'An error occurred processing your request'
        }), 500


def _handle_regular_chat(message, context, model, temperature):
    """Handle regular chat conversation"""
    messages = context + [{'role': 'user', 'content': message}]

    result = ollama_service.chat(messages, model=model, temperature=temperature)

    if result.get('success'):
        return result.get('message', 'No response generated')
    else:
        return f"Error: {result.get('error', 'Failed to generate response')}"


def _handle_aem_chat(message, intent_result, model):
    """Handle AEM-related chat"""
    entities = intent_result.get('extracted_entities', {})

    if intent_result['intent'] == Intent.AEM_QUERY:
        # User wants to find/list pages
        path = entities.get('path', '/content')
        return f"To browse AEM pages, please use the AEM page picker. Default path: {path}\n\nYou can search for pages under any path in your AEM instance."

    elif intent_result['intent'] == Intent.AEM_COMPLIANCE:
        # User wants compliance check
        return "To run a compliance check:\n1. Use the AEM page picker to select pages\n2. Choose which compliance categories to check\n3. Click 'Run Compliance Check'\n\nI'll analyze the pages for accessibility, SEO, performance, security, and more!"

    else:
        # General AEM question
        system_msg = "You are an AEM (Adobe Experience Manager) expert. Answer questions about AEM clearly and accurately."
        messages = [
            {'role': 'system', 'content': system_msg},
            {'role': 'user', 'content': message}
        ]
        result = ollama_service.chat(messages, model=model, temperature=0.5)
        return result.get('message', 'Unable to answer AEM question')


def _handle_web_search(message, model):
    """Handle web search"""
    result = web_search_service.search_and_summarize(message, model=model)

    if result.get('success'):
        summary = result.get('summary', '')
        sources = result.get('sources', [])

        response = summary
        if sources:
            response += "\n\nSources:\n"
            for i, source in enumerate(sources[:3], 1):
                response += f"{i}. {source}\n"

        return response
    else:
        return f"Web search failed: {result.get('error', 'Unknown error')}"


# ==================== FILE UPLOAD ENDPOINTS ====================

@app.route('/api/file/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        question = request.form.get('question', None)
        model = request.form.get('model', Config.DEFAULT_MODEL)

        # Save file
        save_result = file_service.save_uploaded_file(file)

        if not save_result.get('success'):
            return jsonify(save_result), 400

        # Process file
        process_result = file_service.process_file(
            save_result['filepath'],
            save_result['original_filename'],
            question,
            model
        )

        # Cleanup
        file_service.cleanup_file(save_result['filepath'])

        if process_result.get('success'):
            return jsonify(process_result)
        else:
            return jsonify(process_result), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== AEM ENDPOINTS ====================

@app.route('/api/aem/query', methods=['POST'])
def query_aem_pages():
    """Query AEM pages"""
    try:
        data = request.json
        path = data.get('path', '/content')
        depth = data.get('depth', 3)
        include_templates = data.get('include_templates')
        exclude_templates = data.get('exclude_templates')

        result = aem_service.query_pages(
            path=path,
            depth=depth,
            include_templates=include_templates,
            exclude_templates=exclude_templates
        )

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/aem/page/<path:page_path>', methods=['GET'])
def get_aem_page(page_path):
    """Get specific AEM page content"""
    try:
        # Ensure path starts with /
        if not page_path.startswith('/'):
            page_path = '/' + page_path

        result = aem_service.get_page_content(page_path)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/aem/compliance/check', methods=['POST'])
def check_compliance():
    """Run compliance check on AEM pages"""
    try:
        data = request.json
        page_paths = data.get('page_paths', [])
        categories = data.get('categories')
        model = data.get('model', Config.DEFAULT_MODEL)

        if not page_paths:
            return jsonify({'error': 'No pages specified'}), 400

        # Run compliance checks
        if len(page_paths) == 1:
            results = [compliance_service.check_page_compliance(
                page_paths[0], categories, model
            )]
        else:
            results = compliance_service.check_multiple_pages(
                page_paths, categories, model
            )

        # Generate summary
        summary = compliance_service.get_summary_statistics(results)

        # Convert results to dict for JSON serialization
        results_dict = [result.dict() for result in results]

        return jsonify({
            'results': results_dict,
            'summary': summary,
            'export_available': True
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/aem/compliance/export', methods=['POST'])
def export_compliance():
    """Export compliance results"""
    try:
        data = request.json
        format_type = data.get('format', 'csv')
        results_data = data.get('results', [])
        include_details = data.get('include_details', True)

        if not results_data:
            return jsonify({'error': 'No results to export'}), 400

        # Convert dict back to ComplianceResult objects
        from models.schemas import ComplianceResult
        results = [ComplianceResult(**r) for r in results_data]

        # Export
        export_result = export_service.export_results(
            results,
            format=format_type,
            include_details=include_details
        )

        if export_result.get('success'):
            # Return file for download
            return send_file(
                export_result['file_path'],
                as_attachment=True,
                download_name=export_result['file_name'],
                mimetype='application/pdf' if format_type == 'pdf' else 'text/csv'
            )
        else:
            return jsonify(export_result), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== WEB SEARCH ENDPOINTS ====================

@app.route('/api/search/web', methods=['POST'])
def search_web():
    """Web search endpoint"""
    try:
        data = request.json
        query = data.get('query', '')
        max_results = data.get('max_results', 5)
        model = data.get('model', Config.DEFAULT_MODEL)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        result = web_search_service.search_and_summarize(
            query, max_results, model
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== VECTOR/RAG ENDPOINTS ====================

@app.route('/api/vector/add', methods=['POST'])
def add_to_vector_store():
    """Add content to vector store"""
    if not vector_service or not vector_service.enabled:
        return jsonify({
            'success': False,
            'error': 'Vector service not available. Please ensure Qdrant is running and embedding models are downloaded.'
        }), 503

    try:
        data = request.json
        text = data.get('text', '')
        metadata = data.get('metadata', {})

        doc_id = vector_service.add_document(text, metadata)

        return jsonify({
            'success': True,
            'document_id': doc_id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vector/search', methods=['POST'])
def search_vector_store():
    """Search vector store"""
    if not vector_service or not vector_service.enabled:
        return jsonify({
            'success': False,
            'error': 'Vector service not available. Please ensure Qdrant is running and embedding models are downloaded.'
        }), 503

    try:
        data = request.json
        query = data.get('query', '')
        limit = data.get('limit', 5)

        results = vector_service.search_similar(query, limit)

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== UTILITY ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    services_status = {
        'ollama': ollama_service.check_health(),
        'aem': aem_service.check_health(),
        'qdrant': vector_service.check_health() if vector_service else False
    }

    # Core services needed
    core_services_healthy = services_status['ollama']

    return jsonify({
        'status': 'healthy' if core_services_healthy else 'degraded',
        'services': services_status,
        'timestamp': datetime.now().isoformat(),
        'notes': {
            'ollama': 'Required - LLM engine',
            'aem': 'Optional - Only needed for AEM features',
            'qdrant': 'Optional - Only needed for vector/RAG features'
        }
    }), 200 if core_services_healthy else 503


@app.route('/api/models', methods=['GET'])
def list_models():
    """List available Ollama models"""
    models = ollama_service.list_models()
    return jsonify({'models': models})


@app.route('/api/conversation/clear/<conversation_id>', methods=['POST'])
def clear_conversation(conversation_id):
    """Clear conversation memory"""
    langchain_service.clear_memory(conversation_id)
    return jsonify({'success': True, 'message': 'Conversation cleared'})


@app.route('/api/conversation/list', methods=['GET'])
def list_conversations():
    """List all conversation IDs"""
    conversations = langchain_service.get_all_conversations()
    return jsonify({'conversations': conversations})


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 AEM Compliance Chatbot Backend Starting...")
    print("=" * 70)
    print(f"📡 Ollama: {Config.OLLAMA_HOST}")
    print(f"🏢 AEM: {Config.AEM_HOST}")
    print(f"💾 Qdrant: {Config.QDRANT_HOST}:{Config.QDRANT_PORT}")
    print(f"🌐 Server: http://localhost:{Config.FLASK_PORT}")
    print("=" * 70)
    print("\nEndpoints available:")
    print("  POST /api/chat - Main chat interface")
    print("  POST /api/file/upload - File upload")
    print("  POST /api/aem/query - Query AEM pages")
    print("  POST /api/aem/compliance/check - Run compliance check")
    print("  POST /api/aem/compliance/export - Export results")
    print("  POST /api/search/web - Web search")
    print("  GET  /api/health - Health check")
    print("=" * 70)
    print("\n")

    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )