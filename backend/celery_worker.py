"""Entry point for the Celery worker and beat scheduler.

    celery -A celery_worker.celery worker --loglevel=info --pool=solo
    celery -A celery_worker.celery beat   --loglevel=info

--pool=solo is required on Windows; the default prefork pool does not work there.
"""
from app import create_app
from extensions import celery

# Importing the app configures the celery singleton and installs ContextTask.
flask_app = create_app()

# Ensure the task modules are imported so the worker registers them.
import tasks  # noqa: E402,F401

__all__ = ['celery']
