"""
File Service V2 - Enhanced with query support
Handles file uploads with simultaneous question answering
"""
import os
from typing import Dict, Optional
from PyPDF2 import PdfReader
from docx import Document
from services.ollama_service import OllamaService
from config import Config


class FileService:
    def __init__(self):
        self.upload_folder = Config.UPLOAD_FOLDER
        self.allowed_extensions = Config.ALLOWED_EXTENSIONS
        self.max_file_size = Config.MAX_FILE_SIZE
        self.ollama_service = OllamaService()
        os.makedirs(self.upload_folder, exist_ok=True)

    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract PDF text: {str(e)}")

    def extract_text_from_docx(self, filepath: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(filepath)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract DOCX text: {str(e)}")

    def extract_text_from_txt(self, filepath: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Failed to read TXT file: {str(e)}")

    def process_file(
            self,
            filepath: str,
            filename: str,
            question: Optional[str] = None,
            model: str = "gemma:2b",
            task: str = "analyze"
    ) -> Dict:
        """
        Process uploaded file with optional task

        Args:
            filepath: Path to the file
            filename: Original filename
            question: User's question about the file
            model: Ollama model to use
            task: Task to perform (analyze, summarize, extract, translate, qa)

        Returns:
            Dictionary with extracted content and answer
        """
        # Get file extension
        ext = filename.rsplit('.', 1)[1].lower()

        # Extract text based on file type
        try:
            if ext == 'pdf':
                content = self.extract_text_from_pdf(filepath)
            elif ext == 'docx':
                content = self.extract_text_from_docx(filepath)
            elif ext in ['txt', 'md']:
                content = self.extract_text_from_txt(filepath)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {ext}'
                }

            # Get file statistics
            file_stats = os.stat(filepath)
            word_count = len(content.split())
            char_count = len(content)

            metadata = {
                'filename': filename,
                'file_type': ext,
                'file_size': file_stats.st_size,
                'word_count': word_count,
                'character_count': char_count
            }

            # Process based on task
            answer = None
            preview = content[:500] + "..." if len(content) > 500 else content

            if question or task != "analyze":
                answer = self._perform_task(content, question, task, model)

            return {
                'success': True,
                'content': content,
                'preview': preview,
                'answer': answer,
                'metadata': metadata,
                'task': task
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _perform_task(
            self,
            content: str,
            question: Optional[str],
            task: str,
            model: str
    ) -> str:
        """
        Perform specific task on file content

        Args:
            content: Extracted file content
            question: User's question
            task: Task type
            model: Model to use

        Returns:
            Task result
        """
        # Truncate content if too long
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n...[content truncated]"

        # Task-specific prompts
        task_prompts = {
            'summarize': f"""Summarize the following document in a clear, concise manner:

Document:
{content}

Provide a comprehensive summary highlighting the key points.""",

            'extract': f"""Extract and list the key information from this document:

Document:
{content}

Extract:
- Main topics
- Important facts
- Key takeaways
- Action items (if any)""",

            'translate': f"""Translate the following document to English (if not already in English):

Document:
{content}

Provide an accurate translation.""",

            'qa': f"""Document Content:
{content}

Question: {question}

Answer the question based ONLY on the information in the document above. If the answer cannot be found, say so clearly.""",

            'analyze': f"""Analyze this document and provide insights:

Document:
{content}

Provide:
1. Document type and purpose
2. Main themes
3. Key insights
4. Potential improvements or issues"""
        }

        # Use custom question if provided, otherwise use task prompt
        if question and task == 'qa':
            prompt = task_prompts['qa']
        elif task in task_prompts:
            prompt = task_prompts[task]
        else:
            # Default: answer custom question
            prompt = f"""Document:
{content}

User Question: {question}

Answer the question based on the document content."""

        messages = [
            {'role': 'system', 'content': 'You are a helpful document analysis assistant.'},
            {'role': 'user', 'content': prompt}
        ]

        result = self.ollama_service.chat(messages, model=model, temperature=0.3)

        if result.get('success'):
            return result.get('message', 'No answer generated')
        else:
            return f"Error generating answer: {result.get('error', 'Unknown error')}"

    def save_uploaded_file(self, file) -> Dict:
        """
        Save uploaded file to disk

        Args:
            file: File object from request

        Returns:
            Dictionary with file information
        """
        try:
            if not file or file.filename == '':
                return {
                    'success': False,
                    'error': 'No file provided'
                }

            if not self.allowed_file(file.filename):
                return {
                    'success': False,
                    'error': f'File type not allowed. Allowed types: {", ".join(self.allowed_extensions)}'
                }

            # Generate unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = file.filename
            name_parts = original_name.rsplit('.', 1)
            filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            filepath = os.path.join(self.upload_folder, filename)

            # Save file
            file.save(filepath)

            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > self.max_file_size:
                os.remove(filepath)
                return {
                    'success': False,
                    'error': f'File too large. Maximum size: {self.max_file_size / 1024 / 1024}MB'
                }

            return {
                'success': True,
                'filepath': filepath,
                'filename': filename,
                'original_filename': original_name,
                'size': file_size
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to save file: {str(e)}'
            }

    def cleanup_file(self, filepath: str):
        """Delete uploaded file after processing"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass