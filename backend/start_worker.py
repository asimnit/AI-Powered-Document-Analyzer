"""
Celery Worker Startup Script

Run this to start a Celery worker that processes document tasks
Usage:
    python start_worker.py
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.celery_app import celery_app

if __name__ == "__main__":
    # Start the worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        "--concurrency=10",  # Process 10 documents at a time (optimal for 20-core system)
        "--pool=solo" if sys.platform == "win32" else "--pool=prefork",  # Windows compatibility
    ])
