"""
Celery configuration for the REBORN API.

This module initializes Celery and defines tasks for the application.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Create the Celery app
app = Celery("reborn_api")

# Configure Celery using Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, name="debug_task")
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
    return "Debug task completed"
