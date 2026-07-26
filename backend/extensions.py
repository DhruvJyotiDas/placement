"""Shared extension singletons.

Kept in their own module so models, routes and tasks can all import them
without importing app.py (which would be a circular import).
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from celery import Celery

db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()

# Configured inside create_app(); declared here so @celery.task decorators
# in tasks/jobs.py have something to bind to at import time.
celery = Celery(__name__)
