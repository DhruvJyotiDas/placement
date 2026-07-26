import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Central configuration for the Placement Portal backend."""

    SECRET_KEY = 'placement-portal-secret-key'

    # ── Database (SQLite only, created programmatically) ──────────────
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'placement.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── JWT auth ──────────────────────────────────────────────────────
    JWT_SECRET_KEY = 'placement-portal-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # ── File storage ──────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')

    # ── Redis cache ───────────────────────────────────────────────────
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300

    # ── Celery (Redis broker + backend) ───────────────────────────────
    CELERY_BROKER_URL = 'redis://localhost:6379/1'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
    CELERY_TIMEZONE = 'Asia/Kolkata'

    # ── SMTP / MailHog ────────────────────────────────────────────────
    # Run MailHog (standalone .exe, no install needed) and it listens here.
    # Web UI to read every mail the app sends: http://localhost:8025
    SMTP_HOST = 'localhost'
    SMTP_PORT = 1025
    SMTP_USER = ''          # MailHog needs no auth
    SMTP_PASSWORD = ''
    MAIL_SENDER = 'placement-cell@institute.edu'
    ADMIN_EMAIL = 'admin@ppa.com'

    # ── Seeded admin (created programmatically, no registration) ──────
    ADMIN_PASSWORD = 'admin123'

    # ── Business rules ────────────────────────────────────────────────
    REMINDER_WINDOW_DAYS = 3    # warn students this many days before deadline
