"""Placement Portal Application — Flask API entry point.

Run:  python app.py          (from inside backend/)
"""
import os

from celery.schedules import crontab
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from extensions import db, jwt, cache, celery


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    CORS(app)                       # the Vue dev server lives on another origin

    configure_celery(app)
    register_blueprints(app)
    register_error_handlers(app)

    with app.app_context():
        # The database is created programmatically — never by hand.
        db.create_all()
        seed_admin()

    return app


def configure_celery(app):
    """Bind the Celery singleton to this Flask app's config and context."""
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        timezone=app.config['CELERY_TIMEZONE'],
        beat_schedule={
            'daily-deadline-reminder': {
                'task': 'tasks.daily_reminder',
                'schedule': crontab(hour=18, minute=0),          # every day, 6pm
            },
            'monthly-activity-report': {
                'task': 'tasks.monthly_report',
                'schedule': crontab(day_of_month=1, hour=8, minute=0),
            },
        },
    )

    # Every task runs inside an app context, so tasks can use current_app / db.
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def register_blueprints(app):
    from routes import auth_bp, admin_bp, company_bp, student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(student_bp)

    @app.get('/api/health')
    def health():
        return jsonify(status='ok', service='placement-portal-api')


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_):
        return jsonify(message='Not found'), 404

    @app.errorhandler(500)
    def server_error(_):
        db.session.rollback()
        return jsonify(message='Internal server error'), 500


def seed_admin():
    """The single admin pre-exists and is created in code. No registration."""
    from flask import current_app
    from models import User

    if User.query.filter_by(role='admin').first():
        return

    admin = User(email=current_app.config['ADMIN_EMAIL'], role='admin')
    admin.set_password(current_app.config['ADMIN_PASSWORD'])
    db.session.add(admin)
    db.session.commit()
    print(f'[INIT] Admin created — {admin.email} / '
          f'{current_app.config["ADMIN_PASSWORD"]}')


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
