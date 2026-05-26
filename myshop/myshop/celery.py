import os

from celery import Celery

"""
Celery configuration for the 'myshop' project.

This module initializes the Celery application instance and configures it to use
Django's settings module. It allows you to run asynchronous tasks (like sending
emails or processing orders) using a message broker (e.g., Redis or RabbitMQ).

Key features:
- Loads default Django settings.
- Configures Celery using the 'CELERY_' namespace in settings.py.
- Auto-discovers tasks defined in the 'tasks.py' file of each installed app.
"""

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myshop.settings")

app = Celery("myshop")

# Load task execution settings from the Django settings object.
# namespace='CELERY' means all celery-related configuration keys
# should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
