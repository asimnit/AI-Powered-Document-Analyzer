"""
Test Celery Worker Configuration
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.celery_app import celery_app

print("=" * 60)
print("Celery Configuration Test")
print("=" * 60)
print(f"Broker: {celery_app.conf.broker_url}")
print(f"Backend: {celery_app.conf.result_backend}")
print(f"\nRegistered Tasks:")
print("-" * 60)
for task_name in sorted(celery_app.tasks.keys()):
    if not task_name.startswith('celery.'):
        print(f"  ✓ {task_name}")
print("=" * 60)
