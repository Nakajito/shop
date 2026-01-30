from .celery import app as celery_app

"""
Project initialization module.

This module ensures that the Celery application is loaded when Django starts.
This allows the @shared_task decorator (used in 'orders/tasks.py' and 'payment/tasks.py')
to use this app instance without creating a circular dependency.

Exposes:
    celery_app: The instance of the Celery application defined in 'celery.py'.
"""

__all__ = ["celery_app"]
