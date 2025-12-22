"""
Development Server Runner

Starts FastAPI server with optimized reload settings.
Only watches application code, ignores venv, logs, and cache directories.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app"],  # Only watch app directory
        reload_excludes=[
            "*.log",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "venv",
            "logs",
            ".git",
            "alembic/versions/__pycache__"
        ],
        log_level="info"
    )
