"""Role-based access control on top of JWT."""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import User, CompanyProfile, StudentProfile


def role_required(*roles):
    """Guard a route so only the given role(s) may call it.

    The decorated view receives the authenticated User as its first argument.
    Deactivated accounts are rejected even with a valid token.
    """
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            user = User.query.get(int(get_jwt_identity()))
            if not user or user.role not in roles:
                return jsonify(message='Forbidden: insufficient role'), 403
            if not user.is_active:
                return jsonify(message='Your account has been deactivated'), 403
            return fn(user, *args, **kwargs)
        return decorated
    return wrapper


def current_company(user):
    return CompanyProfile.query.filter_by(user_id=user.id).first()


def current_student(user):
    return StudentProfile.query.filter_by(user_id=user.id).first()
