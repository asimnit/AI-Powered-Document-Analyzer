"""
Core Configuration Module

This file manages all application settings using Pydantic.
- Loads from environment variables (.env file)
- Provides type checking and validation
- Centralizes all configuration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application Settings
    
    All settings can be overridden by environment variables.
    Example: DATABASE_URL in .env will override database_url here
    """
    
    # Application
    APP_NAME: str = "AI Document Analyzer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/docanalyzer"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - Allow frontend to access backend
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".xlsx", ".txt", ".png", ".jpg", ".jpeg"}
    
    # Tesseract OCR Configuration
    TESSERACT_CMD: Optional[str] = None  # Set in .env or leave None for auto-detection
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = "YOUR_AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY: str = "YOUR_AWS_SECRET_ACCESS_KEY"
    AWS_REGION: str = "us-east-1"  # Change to your preferred region
    S3_BUCKET_NAME: str = "your-document-analyzer-bucket"
    S3_UPLOAD_ENABLED: bool = True  # Set to False to use local storage
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "azure"  # azure, openai, ollama (future)
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = "https://your-resource.openai.azure.com/"
    AZURE_OPENAI_API_KEY: str = "your-azure-openai-api-key"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-small"  # Your deployment name
    AZURE_CHAT_DEPLOYMENT: str = "gpt-4o-mini"  # Your chat model deployment name
    
    # Embedding Configuration
    EMBEDDING_DIMENSION: int = 1536  # text-embedding-3-small dimension
    EMBEDDING_BATCH_SIZE: int = 100  # Process 100 texts at a time
    
    # RAG Configuration
    RAG_TOP_K: int = 10  # Retrieve top 10 most relevant chunks across all stores
    RAG_CONTEXT_WINDOW: int = 10  # Max chunks to include in context
    RAG_TEMPERATURE: float = 0.7  # LLM temperature for chat (0.0-2.0)
    RAG_MAX_TOKENS: int = 1000  # Max tokens in response
    
    # Chat Configuration
    MAX_STORES_PER_CONVERSATION: int = 5  # Maximum stores attachable to one conversation
    MAX_CONVERSATION_HISTORY: int = 10  # Number of previous messages to include in context
    CHAT_MODEL_TEMPERATURE: float = 0.7  # Chat model temperature
    MAX_TOKENS_PER_RESPONSE: Optional[int] = None  # No limit - let model use its maximum capacity
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True


# Create single instance to be imported elsewhere
settings = Settings()
