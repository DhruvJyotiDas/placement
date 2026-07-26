"""Login + self-registration for students and companies.

Admin is seeded programmatically and can never be registered here.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from extensions import db, cache
from models import User, CompanyProfile, StudentProfile

auth_bp = Blueprint('auth', __name__, url_prefix='/api')


@auth_bp.post('/register')
def register():
    data = request.get_json() or {}
    role = data.get('role')
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if role not in ('student', 'company'):
        return jsonify(message='You may only register as a student or a company'), 400
    if not email or not password:
        return jsonify(message='Email and password are required'), 400
    if User.query.filter_by(email=email).first():
        return jsonify(message='That email is already registered'), 409

    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()          # assigns user.id without committing

    if role == 'company':
        if not (data.get('company_name') or '').strip():
            return jsonify(message='Company name is required'), 400
        db.session.add(CompanyProfile(
            user_id=user.id,
            company_name=data['company_name'].strip(),
            industry=data.get('industry', ''),
            location=data.get('location', ''),
            hr_contact=data.get('hr_contact', ''),
            website=data.get('website', ''),
            description=data.get('description', ''),
        ))
        msg = 'Registered. Your company is pending admin approval.'
    else:
        if not (data.get('name') or '').strip():
            return jsonify(message='Name is required'), 400
        roll = (data.get('roll_number') or '').strip()
        if roll and StudentProfile.query.filter_by(roll_number=roll).first():
            return jsonify(message='That roll number is already registered'), 409
        db.session.add(StudentProfile(
            user_id=user.id,
            name=data['name'].strip(),
            roll_number=roll,
            branch=data.get('branch', ''),
            cgpa=float(data.get('cgpa') or 0),
            year=int(data.get('year') or 1),
            skills=data.get('skills', ''),
        ))
        msg = 'Registered successfully. You may now log in.'

    db.session.commit()
    cache.delete('admin_stats')
    return jsonify(message=msg), 201


@auth_bp.post('/login')
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(data.get('password') or ''):
        return jsonify(message='Invalid email or password'), 401
    if not user.is_active:
        return jsonify(message='Your account has been deactivated by the admin'), 403

    return jsonify(
        token=create_access_token(identity=str(user.id)),
        role=user.role,
        email=user.email,
        user_id=user.id,
    )
