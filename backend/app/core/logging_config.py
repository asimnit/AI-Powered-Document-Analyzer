"""
Logging Configuration

Centralized logging setup for the application.
- Configures log format with timestamps
- Sets up console and file handlers
- Creates logs directory automatically
- Supports different log levels for dev/prod
"""

import logging
import sys
from pathlib import Path
from typing import Any

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure application logging
    
    Sets up:
    - Console handler (stdout) - for development
    - File handler (logs/app.log) - for production
    - Colored format with timestamps
    - Log rotation (future enhancement)
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Define log format
    # Example: 2025-12-21 10:30:45 | INFO     | app.api.auth:45 | User logged in
    log_format = (
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s:%(lineno)d | %(message)s"
    )
    
    # Date format
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Determine log level based on environment
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Create handlers with UTF-8 encoding to support emoji characters
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    # Set UTF-8 encoding for console to support Unicode characters
    if hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8')
    
    file_handler = logging.FileHandler(log_dir / "app.log", encoding='utf-8')
    file_handler.setLevel(logging.INFO)  # Always log INFO+ to file
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)  # Silence file change spam
    logging.getLogger("botocore").setLevel(logging.WARNING)  # Silence AWS SDK debug logs


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened")
    
    Args:
        name: Usually __name__ to get module name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
