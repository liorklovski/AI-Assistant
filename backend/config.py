import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Basic Flask/FastAPI configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # API Configuration
    API_TITLE = "AI Chat Assistant MVP"
    API_VERSION = "1.0.0"
    
    # CORS Configuration
    CORS_ORIGINS = [
        'http://localhost:3000', 
        'http://127.0.0.1:3000'
    ]
    
    # AI Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    DEEPAI_API_KEY = os.environ.get('DEEPAI_API_KEY')
    USE_DUMMY_AI = os.environ.get('USE_DUMMY_AI', 'true').lower() == 'true'  # Fallback option
    
    # Retry Configuration
    GEMINI_MAX_RETRIES = 2
    DEEPAI_MAX_RETRIES = 2
    API_TIMEOUT_SECONDS = 10
    
    # Processing Configuration
    MIN_PROCESSING_TIME = 1  # seconds
    MAX_PROCESSING_TIME = 3  # seconds  
    DEFAULT_PROCESSING_TIME = 2  # seconds
    
    # Job Configuration
    MAX_JOBS_IN_MEMORY = 1000  # For MVP, limit in-memory storage
    JOB_CLEANUP_INTERVAL = 3600  # seconds (1 hour)