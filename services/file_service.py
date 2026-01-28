"""
File Service - Handles file uploads and processing
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
            model: str = "gemma:2b"
    ) -> Dict:
        """
        Process uploaded file and optionally answer questions about it

        Args:
            filepath: Path to the file
            filename: Original filename
            question: Optional question about the file
            model: Ollama model to use

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

            # If question is provided, answer it using Ollama
            answer = None
            if question and content:
                answer = self._answer_question(content, question, model)

            return {
                'success': True,
                'content': content,
                'answer': answer,
                'metadata': metadata
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _answer_question(
            self,
            content: str,
            question: str,
            model: str
    ) -> str:
        """
        Answer a question about the file content using Ollama

        Args:
            content: Extracted file content
            question: User's question
            model: Model to use

        Returns:
            Answer to the question
        """
        # Truncate content if too long
        max_content_length = 8000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n...[content truncated]"

        system_message = """You are a helpful assistant analyzing document content.
Answer questions based on the provided document accurately and concisely.
If the answer cannot be found in the document, say so clearly."""

        user_message = f"""Document Content:
{content}

Question: {question}

Please provide a clear and accurate answer based on the document content."""

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
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