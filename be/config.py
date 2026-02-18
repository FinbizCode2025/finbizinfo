from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Keys
    _GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

    # Model Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-pro')

    # LangChain Configuration
    LANGCHAIN_TRACING_V2 = os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
    LANGCHAIN_ENDPOINT = os.getenv('LANGCHAIN_ENDPOINT')
    LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')
    LANGCHAIN_PROJECT = os.getenv('LANGCHAIN_PROJECT')

    @classmethod
    def set_api_key(cls, api_key: str):
        cls._GOOGLE_API_KEY = api_key

    @property
    def GOOGLE_API_KEY(self):
        return self._GOOGLE_API_KEY

    # File Storage Configuration
    BASE_DIR = Path(__file__).resolve().parent
    UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', 'uploads'))
    SESSIONS_DIR = Path(os.getenv('SESSIONS_DIR', 'uploads/sessions'))

    # Ensure directories exist
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Tesseract Configuration
    TESSERACT_PATH = os.getenv('TESSERACT_PATH', r"C:\Program Files\Tesseract-OCR\tesseract.exe")

    # Server Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    PORT = int(os.getenv('PORT', 5002))
    HOST = os.getenv('HOST', '127.0.0.1')

    @classmethod
    def validate(cls):
        """Validate required configuration settings."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY must be set in .env file")
        
        if not Path(cls.TESSERACT_PATH).exists():
            raise ValueError(f"Tesseract not found at {cls.TESSERACT_PATH}")
        
        return True