"""Admin (Institute Placement Cell) endpoints."""
import redis
from flask import Blueprint, current_app, request, jsonify

from extensions import db, cache
from models import User, CompanyProfile, StudentProfile, PlacementDrive, Application
from security import role_required
from tasks.jobs import monthly_report

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _delete_with_user(profile):
    """Hard-delete a company/student profile along with its login account."""
    user = profile.user
    db.session.delete(profile)
    db.session.delete(user)


def _bust_caches():
    cache.delete('admin_stats')
    cache.delete('open_drives')


# ── Dashboard ─────────────────────────────────────────────────────────

@admin_bp.get('/stats')
@role_required('admin')
@cache.cached(timeout=120, key_prefix='admin_stats')
def stats(user):
    """Headline counts. Cached in Redis for 2 minutes, busted on any write."""
    return jsonify(
        total_students=StudentProfile.query.count(),
        total_companies=CompanyProfile.query.count(),
        total_drives=PlacementDrive.query.count(),
        total_applications=Application.query.count(),
        pending_companies=CompanyProfile.query.filter_by(approval_status='pending').count(),
        pending_drives=PlacementDrive.query.filter_by(status='pending').count(),
        students_selected=Application.query.filter_by(status='selected').count(),
    )


@admin_bp.post('/report')
@role_required('admin')
def trigger_report(user):
    """Admin-triggered version of the monthly report job (same task as the schedule)."""
    try:
        redis.Redis.from_url(
            current_app.config['CELERY_BROKER_URL'], socket_connect_timeout=2,
        ).ping()
    except redis.RedisError:
        return jsonify(message='Could not reach Redis — make sure redis-server is running'), 503

    task = monthly_report.delay()
    return jsonify(message='Report queued — check your email shortly', task_id=task.id), 202


# ── Companies ─────────────────────────────────────────────────────────

@admin_bp.get('/companies')
@role_required('admin')
def list_companies(user):
    q = (request.args.get('q') or '').strip()
    status = request.args.get('status')          # pending | approved | rejected

    query = CompanyProfile.query
    if q:
        query = query.filter(db.or_(
            CompanyProfile.company_name.ilike(f'%{q}%'),
            CompanyProfile.industry.ilike(f'%{q}%'),
        ))
    if status:
        query = query.filter_by(approval_status=status)

    return jsonify([c.to_dict() for c in query.order_by(CompanyProfile.id).all()])


@admin_bp.delete('/companies/<int:cid>')
@role_required('admin')
def delete_company(user, cid):
    company = CompanyProfile.query.get_or_404(cid)
    name = company.company_name
    _delete_with_user(company)
    db.session.commit()
    _bust_caches()
    return jsonify(message=f'{name} permanently removed')


@admin_bp.put('/companies/<int:cid>/<action>')
@role_required('admin')
def company_action(user, cid, action):
    company = CompanyProfile.query.get_or_404(cid)

    if action == 'approve':
        company.approval_status = 'approved'
        message = f'{company.company_name} approved'

    elif action == 'reject':
        company.approval_status = 'rejected'
        message = f'{company.company_name} rejected'

    elif action == 'blacklist':
        company.is_blacklisted = True
        company.user.is_active = False
        # Wireframe rule: blacklisting a company cancels all of its drives.
        cancelled = 0
        for drive in company.drives:
            if drive.status in ('pending', 'approved'):
                drive.status = 'cancelled'
                cancelled += 1
        message = f'{company.company_name} blacklisted — {cancelled} drive(s) cancelled'

    elif action == 'unblacklist':
        company.is_blacklisted = False
        company.user.is_active = True
        message = f'{company.company_name} restored'

    else:
        return jsonify(message='Unknown action'), 400

    db.session.commit()
    _bust_caches()
    return jsonify(message=message)


# ── Students ──────────────────────────────────────────────────────────

@admin_bp.get('/students')
@role_required('admin')
def list_students(user):
    q = (request.args.get('q') or '').strip()

    query = StudentProfile.query.join(User)
    if q:
        query = query.filter(
            db.or_(
                StudentProfile.name.ilike(f'%{q}%'),
                StudentProfile.roll_number.ilike(f'%{q}%'),
                StudentProfile.branch.ilike(f'%{q}%'),
                User.email.ilike(f'%{q}%'),
            )
        )

    return jsonify([s.to_dict() for s in query.order_by(StudentProfile.id).all()])


@admin_bp.delete('/students/<int:sid>')
@role_required('admin')
def delete_student(user, sid):
    student = StudentProfile.query.get_or_404(sid)
    name = student.name
    _delete_with_user(student)
    db.session.commit()
    _bust_caches()
    return jsonify(message=f'{name} permanently removed')


@admin_bp.put('/students/<int:sid>/<action>')
@role_required('admin')
def student_action(user, sid, action):
    student = StudentProfile.query.get_or_404(sid)

    if action == 'blacklist':
        student.is_blacklisted = True
        student.user.is_active = False
        message = f'{student.name} blacklisted and deactivated'
    elif action == 'unblacklist':
        student.is_blacklisted = False
        student.user.is_active = True
        message = f'{student.name} restored'
    else:
        return jsonify(message='Unknown action'), 400

    db.session.commit()
    _bust_caches()
    return jsonify(message=message)


# ── Drives ────────────────────────────────────────────────────────────

@admin_bp.get('/drives')
@role_required('admin')
def list_drives(user):
    q = (request.args.get('q') or '').strip()
    status = request.args.get('status')

    query = PlacementDrive.query.join(CompanyProfile)
    if q:
        query = query.filter(
            db.or_(
                PlacementDrive.job_title.ilike(f'%{q}%'),
                PlacementDrive.drive_name.ilike(f'%{q}%'),
                CompanyProfile.company_name.ilike(f'%{q}%'),
            )
        )
    if status:
        query = query.filter(PlacementDrive.status == status)

    return jsonify([d.to_dict() for d in query.order_by(PlacementDrive.id).all()])


@admin_bp.put('/drives/<int:did>/<action>')
@role_required('admin')
def drive_action(user, did, action):
    drive = PlacementDrive.query.get_or_404(did)

    if action == 'approve':
        if drive.company.approval_status != 'approved':
            return jsonify(message='Approve the company before approving its drives'), 400
        if drive.company.is_blacklisted:
            return jsonify(message='Cannot approve a drive from a blacklisted company'), 400
        drive.status = 'approved'
    elif action == 'reject':
        drive.status = 'rejected'
    elif action == 'close':
        drive.status = 'closed'
    else:
        return jsonify(message='Unknown action'), 400

    db.session.commit()
    _bust_caches()
    return jsonify(message=f'Drive "{drive.drive_name}" {action}d')


@admin_bp.delete('/drives/<int:did>')
@role_required('admin')
def delete_drive(user, did):
    drive = PlacementDrive.query.get_or_404(did)
    name = drive.drive_name
    db.session.delete(drive)
    db.session.commit()
    _bust_caches()
    return jsonify(message=f'Drive "{name}" permanently removed')


# ── Applications ──────────────────────────────────────────────────────

@admin_bp.get('/applications')
@role_required('admin')
def list_applications(user):
    q = (request.args.get('q') or '').strip()

    query = Application.query.join(StudentProfile).join(PlacementDrive)
    if q:
        query = query.filter(
            db.or_(
                StudentProfile.name.ilike(f'%{q}%'),
                PlacementDrive.job_title.ilike(f'%{q}%'),
            )
        )

    apps = query.order_by(Application.application_date.desc()).all()
    return jsonify([a.to_dict() for a in apps])
