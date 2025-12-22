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
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = "YOUR_AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY: str = "YOUR_AWS_SECRET_ACCESS_KEY"
    AWS_REGION: str = "us-east-1"  # Change to your preferred region
    S3_BUCKET_NAME: str = "your-document-analyzer-bucket"
    S3_UPLOAD_ENABLED: bool = True  # Set to False to use local storage
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True


# Create single instance to be imported elsewhere
settings = Settings()
