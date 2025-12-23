"""
Celery configuration for asynchronous task processing
"""
from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "document_analyzer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    result_expires=3600,  # Results expire after 1 hour
)

# Task routing - all tasks go to celery queue (Celery's default)
celery_app.conf.task_routes = {
    "app.tasks.*": {"queue": "celery"},
}

# Import tasks to register them with Celery
# This ensures tasks are loaded when the celery app is imported
from app.tasks import document_tasks  # noqa: E402
