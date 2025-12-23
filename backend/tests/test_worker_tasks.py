"""
Quick test to verify worker can see registered tasks
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import celery app (this should register tasks)
from app.celery_app import celery_app

print("Celery Broker:", celery_app.conf.broker_url)
print("\nRegistered Tasks:")
for name in sorted(celery_app.tasks.keys()):
    if not name.startswith('celery.'):
        print(f"  - {name}")

# Check if our specific task is registered
task_name = "app.tasks.process_document"
if task_name in celery_app.tasks:
    print(f"\n✅ Task '{task_name}' is registered!")
else:
    print(f"\n❌ Task '{task_name}' NOT found!")
