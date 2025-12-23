"""
Development Server Runner

Starts FastAPI server only.
Run Celery worker separately with: python start_worker.py
"""

import uvicorn
import sys


if __name__ == "__main__":
    print("=" * 60)
    print("Starting AI Document Analyzer - FastAPI Server")
    print("=" * 60)
    print(f"Python:       {sys.executable}")
    print("FastAPI:      http://localhost:8000")
    print()
    print("⚠️  Remember to start Celery worker separately:")
    print("   python start_worker.py")
    print("=" * 60)
    print()
    
    try:
        # Start FastAPI (blocking)
        print("🚀 Starting FastAPI server...\n")
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
    except KeyboardInterrupt:
        print("\n\n⚠️  Shutting down...")
        print("Shutdown complete")
