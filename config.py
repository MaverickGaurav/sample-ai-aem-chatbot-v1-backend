"""
Configuration settings for AEM Compliance Chatbot
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 8000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # AEM Configuration
    AEM_HOST = os.getenv('AEM_HOST', 'http://localhost:4502')
    AEM_USERNAME = os.getenv('AEM_USERNAME', 'admin')
    AEM_PASSWORD = os.getenv('AEM_PASSWORD', 'admin')
    AEM_TIMEOUT = int(os.getenv('AEM_TIMEOUT', 30))

    # Ollama Configuration
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gemma3')
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', 60))

    # Qdrant Configuration
    QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6333))
    QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'aem_content')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

    # File Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 10485760))  # 10MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'md'}

    # Web Search Configuration
    SEARCH_PROVIDER = os.getenv('SEARCH_PROVIDER', 'duckduckgo')
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 5))

    # LangChain Configuration
    MEMORY_MAX_TOKENS = int(os.getenv('MEMORY_MAX_TOKENS', 2000))
    CONTEXT_WINDOW = int(os.getenv('CONTEXT_WINDOW', 10))

    # Compliance Configuration
    COMPLIANCE_THRESHOLD = float(os.getenv('COMPLIANCE_THRESHOLD', 0.7))
    MAX_CONCURRENT_CHECKS = int(os.getenv('MAX_CONCURRENT_CHECKS', 5))

    # Intent Detection Configuration
    INTENT_CONFIDENCE_THRESHOLD = float(os.getenv('INTENT_CONFIDENCE_THRESHOLD', 0.6))

    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}