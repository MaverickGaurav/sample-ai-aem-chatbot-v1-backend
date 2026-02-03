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


from services.image_generation_service import ImageGenerationService
from services.workflow_service import WorkflowService
from services.metadata_service import MetadataService

# Initialize new services (add after existing service initialization)
try:
    image_service = ImageGenerationService()
    print("✓ Image Generation Service initialized")
except Exception as e:
    print(f"⚠ Image service disabled: {e}")
    image_service = None

try:
    workflow_service = WorkflowService()
    print("✓ Workflow Service initialized")
except Exception as e:
    print(f"⚠ Workflow service disabled: {e}")
    workflow_service = None

try:
    metadata_service = MetadataService()
    print("✓ Metadata Service initialized")
except Exception as e:
    print(f"⚠ Metadata service disabled: {e}")
    metadata_service = None


# ==================== ENHANCED FILE UPLOAD ENDPOINT ====================

@app.route('/api/file/upload', methods=['POST'])
def upload_file_v2():
    """Handle file upload with question/task support"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        question = request.form.get('question', None)
        task = request.form.get('task', 'analyze')
        model = request.form.get('model', Config.DEFAULT_MODEL)

        # Save file
        save_result = file_service.save_uploaded_file(file)

        if not save_result.get('success'):
            return jsonify(save_result), 400

        # Process file with task
        process_result = file_service.process_file(
            save_result['filepath'],
            save_result['original_filename'],
            question,
            model,
            task
        )

        # Cleanup
        file_service.cleanup_file(save_result['filepath'])

        if process_result.get('success'):
            return jsonify(process_result)
        else:
            return jsonify(process_result), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== IMAGE GENERATION ENDPOINTS ====================

@app.route('/api/image/generate', methods=['POST'])
def generate_image():
    """Generate image from text prompt"""
    if not image_service:
        return jsonify({
            'success': False,
            'error': 'Image generation service not available'
        }), 503

    try:
        data = request.json
        prompt = data.get('prompt', '')
        style = data.get('style', 'realistic')
        width = data.get('width', 512)
        height = data.get('height', 512)
        provider = data.get('provider', 'local')

        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        result = image_service.generate_image(
            prompt=prompt,
            style=style,
            width=width,
            height=height,
            provider=provider
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/image/enhance-prompt', methods=['POST'])
def enhance_prompt():
    """Enhance a basic prompt using Ollama"""
    if not image_service:
        return jsonify({
            'success': False,
            'error': 'Image generation service not available'
        }), 503

    try:
        data = request.json
        basic_prompt = data.get('prompt', '')
        model = data.get('model', Config.DEFAULT_MODEL)

        if not basic_prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        enhanced = image_service.enhance_prompt(basic_prompt, model)

        return jsonify({
            'success': True,
            'original': basic_prompt,
            'enhanced': enhanced
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/image/styles', methods=['GET'])
def get_image_styles():
    """Get available image styles"""
    if not image_service:
        return jsonify([]), 503

    return jsonify(image_service.get_style_presets())


@app.route('/api/image/health', methods=['GET'])
def image_generation_health():
    """Check image generation service health"""
    if not image_service:
        return jsonify({'available': False})

    return jsonify(image_service.check_health())


# ==================== WORKFLOW ENDPOINTS ====================

@app.route('/api/workflow/list', methods=['GET'])
def list_workflows():
    """List available AEM workflows"""
    if not workflow_service:
        return jsonify({
            'success': False,
            'error': 'Workflow service not available'
        }), 503

    try:
        result = workflow_service.list_workflows()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflow/start', methods=['POST'])
def start_workflow():
    """Start workflow on a page"""
    if not workflow_service:
        return jsonify({
            'success': False,
            'error': 'Workflow service not available'
        }), 503

    try:
        data = request.json
        page_path = data.get('page_path')
        workflow_model = data.get('workflow_model')

        if not page_path or not workflow_model:
            return jsonify({'error': 'page_path and workflow_model required'}), 400

        result = workflow_service.start_workflow(page_path, workflow_model)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== METADATA ENDPOINTS ====================

@app.route('/api/metadata/get', methods=['POST'])
def get_metadata():
    """Get asset metadata"""
    if not metadata_service:
        return jsonify({
            'success': False,
            'error': 'Metadata service not available'
        }), 503

    try:
        data = request.json
        asset_path = data.get('asset_path')

        if not asset_path:
            return jsonify({'error': 'asset_path required'}), 400

        result = metadata_service.get_metadata(asset_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/metadata/update', methods=['POST'])
def update_metadata():
    """Update asset metadata"""
    if not metadata_service:
        return jsonify({
            'success': False,
            'error': 'Metadata service not available'
        }), 503

    try:
        data = request.json
        asset_path = data.get('asset_path')
        metadata = data.get('metadata', {})

        if not asset_path:
            return jsonify({'error': 'asset_path required'}), 400

        result = metadata_service.update_metadata(asset_path, metadata)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== EXPORT ENDPOINT (FIXED) ====================

@app.route('/api/aem/compliance/export', methods=['POST'])
def export_compliance_v2():
    """Export compliance results - FIXED VERSION"""
    try:
        data = request.json
        format_type = data.get('format', 'csv')
        results_data = data.get('results', [])
        include_details = data.get('include_details', True)

        if not results_data:
            return jsonify({'error': 'No results to export'}), 400

        # Export directly with dictionaries (no need to convert to objects)
        export_result = export_service.export_results(
            results_data,  # Pass as-is
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


# ==================== THEME ENDPOINT ====================

@app.route('/api/themes', methods=['GET'])
def get_themes():
    """Get available themes"""
    from services.themes import THEMES
    return jsonify(THEMES)


# ==================== UTILITY ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health_check_v2():
    """Enhanced health check endpoint"""
    services_status = {
        'ollama': ollama_service.check_health(),
        'aem': aem_service.check_health(),
        'qdrant': vector_service.check_health() if vector_service else False,
        'image_generation': image_service.check_health() if image_service else {'available': False},
        'workflow': workflow_service is not None,
        'metadata': metadata_service is not None
    }

    core_services_healthy = services_status['ollama']

    return jsonify({
        'status': 'healthy' if core_services_healthy else 'degraded',
        'services': services_status,
        'timestamp': datetime.now().isoformat(),
        'version': '2.0',
        'notes': {
            'ollama': 'Required - LLM engine',
            'aem': 'Optional - For AEM features',
            'qdrant': 'Optional - For vector/RAG features',
            'image_generation': 'Optional - For image generation',
            'workflow': 'Optional - For AEM workflows',
            'metadata': 'Optional - For asset metadata'
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
    print("\n🎨 V2 New Features:")
    print("  ✓ Enhanced file upload with tasks")
    print("  ✓ Image generation (Stable Diffusion)")
    print("  ✓ AEM workflow management")
    print("  ✓ Asset metadata editor")
    print("  ✓ Fixed CSV/PDF export")
    print("  ✓ Aurora theme support")
    print("=" * 70)
    print("\n")

    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )