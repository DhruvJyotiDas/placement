"""Student endpoints — profile, drive discovery, applications, CSV export."""
import os
from datetime import datetime

from celery.result import AsyncResult
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename

from extensions import db, cache, celery
from models import CompanyProfile, PlacementDrive, Application
from security import role_required, current_student
from tasks.jobs import export_applications_csv
from tasks.mailer import send_email

student_bp = Blueprint('student', __name__, url_prefix='/api/student')

ALLOWED_RESUME_EXTS = {'.pdf', '.doc', '.docx'}


def _open_drive_dicts():
    """Approved, not-yet-expired drives.

    Cached in Redis for 60s. The payload is role-neutral, so it is shared
    across every student; per-student eligibility is layered on afterwards.
    """
    cached = cache.get('open_drives')
    if cached is not None:
        return cached

    drives = (PlacementDrive.query
              .filter(PlacementDrive.status == 'approved')
              .filter(PlacementDrive.deadline >= datetime.utcnow())
              .order_by(PlacementDrive.deadline)
              .all())
    payload = [d.to_dict() for d in drives]
    cache.set('open_drives', payload, timeout=60)
    return payload


def _eligibility(drive, student):
    """Same rule as PlacementDrive.check_eligibility, applied to a cached dict."""
    if student.cgpa < drive['min_cgpa']:
        return f"Requires a minimum CGPA of {drive['min_cgpa']} (yours is {student.cgpa})"
    if student.year != drive['eligible_year']:
        return f"Open to year {drive['eligible_year']} students only"
    if drive['eligible_branches']:
        allowed = [b.strip().lower() for b in drive['eligible_branches'].split(',')]
        if 'all' not in allowed and (student.branch or '').lower() not in allowed:
            return f"Open to these branches only: {drive['eligible_branches']}"
    return None


# ── Profile ───────────────────────────────────────────────────────────

@student_bp.get('/profile')
@role_required('student')
def get_profile(user):
    student = current_student(user)
    if not student:
        return jsonify(message='Student profile not found'), 404
    return jsonify(student.to_dict())


@student_bp.put('/profile')
@role_required('student')
def update_profile(user):
    student = current_student(user)
    data = request.get_json() or {}

    student.name = data.get('name', student.name)
    student.branch = data.get('branch', student.branch)
    student.cgpa = float(data.get('cgpa', student.cgpa) or 0)
    student.year = int(data.get('year', student.year) or 1)
    student.skills = data.get('skills', student.skills)

    db.session.commit()
    return jsonify(message='Profile updated', student=student.to_dict())


@student_bp.post('/resume')
@role_required('student')
def upload_resume(user):
    student = current_student(user)

    if 'resume' not in request.files:
        return jsonify(message='No file was uploaded'), 400

    file = request.files['resume']
    if not file.filename:
        return jsonify(message='No file was selected'), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_RESUME_EXTS:
        return jsonify(message='Resume must be a PDF, DOC or DOCX'), 400

    filename = secure_filename(f'{student.roll_number or student.id}_resume{ext}')
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

    student.resume_path = filename
    db.session.commit()
    return jsonify(message='Resume uploaded', resume_path=filename)


@student_bp.get('/resume')
@role_required('student')
def download_own_resume(user):
    student = current_student(user)
    if not student.resume_path:
        return jsonify(message='You have not uploaded a resume yet'), 404
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], student.resume_path)


# ── Drive discovery ───────────────────────────────────────────────────

@student_bp.get('/drives')
@role_required('student')
def browse_drives(user):
    """All approved, open drives — searchable and eligibility-annotated."""
    student = current_student(user)
    q = (request.args.get('q') or '').strip().lower()
    eligible_only = request.args.get('eligible_only') == 'true'

    applied_ids = {a.drive_id for a in student.applications}
    results = []

    for drive in _open_drive_dicts():
        if q and q not in (drive['job_title'] + drive['company_name']
                           + drive['drive_name']).lower():
            continue

        reason = _eligibility(drive, student)
        if eligible_only and reason:
            continue

        results.append({
            **drive,
            'eligible': reason is None,
            'ineligible_reason': reason,
            'already_applied': drive['id'] in applied_ids,
        })

    return jsonify(results)


@student_bp.get('/drives/<int:did>')
@role_required('student')
def drive_detail(user, did):
    student = current_student(user)
    drive = PlacementDrive.query.get_or_404(did)

    if drive.status != 'approved':
        return jsonify(message='That drive is not open'), 404
    return jsonify(drive.to_dict(student=student))


@student_bp.get('/companies/<int:cid>')
@role_required('student')
def company_detail(user, cid):
    """A company's public profile plus its currently open drives."""
    student = current_student(user)
    company = CompanyProfile.query.get_or_404(cid)

    if company.approval_status != 'approved' or company.is_blacklisted:
        return jsonify(message='That company is not available'), 404

    open_drives = [d for d in company.drives if d.is_open()]
    return jsonify(
        company={
            'id': company.id,
            'company_name': company.company_name,
            'description': company.description,
            'website': company.website,
            'hr_contact': company.hr_contact,
        },
        drives=[d.to_dict(student=student) for d in open_drives],
    )


# ── Applying ──────────────────────────────────────────────────────────

@student_bp.post('/drives/<int:did>/apply')
@role_required('student')
def apply(user, did):
    student = current_student(user)
    drive = PlacementDrive.query.get_or_404(did)

    if student.is_blacklisted:
        return jsonify(message='Blacklisted students cannot apply'), 403
    if drive.status != 'approved':
        return jsonify(message='That drive is not open for applications'), 400
    if drive.deadline < datetime.utcnow():
        return jsonify(message='The application deadline has passed'), 400

    # Eligibility is validated before the application is ever created.
    reason = drive.check_eligibility(student)
    if reason:
        return jsonify(message=f'You are not eligible: {reason}'), 400

    # A student may never apply to the same drive twice.
    if Application.query.filter_by(student_id=student.id, drive_id=drive.id).first():
        return jsonify(message='You have already applied to this drive'), 409

    application = Application(student_id=student.id, drive_id=drive.id)
    db.session.add(application)
    db.session.commit()

    send_email(
        drive.company.user.email,
        f'New applicant for "{drive.job_title}"',
        f'<p><b>{student.name}</b> ({student.roll_number}, {student.branch}, '
        f'CGPA {student.cgpa}) just applied to your drive '
        f'"<b>{drive.drive_name}</b>".</p>',
    )

    cache.delete('admin_stats')
    return jsonify(message=f'Applied to "{drive.job_title}"',
                   application=application.to_dict()), 201


@student_bp.get('/applications')
@role_required('student')
def my_applications(user):
    """Complete placement history for this student."""
    student = current_student(user)
    apps = (Application.query
            .filter_by(student_id=student.id)
            .order_by(Application.application_date.desc())
            .all())
    return jsonify([a.to_dict() for a in apps])


# ── Async CSV export ──────────────────────────────────────────────────

@student_bp.post('/export')
@role_required('student')
def trigger_export(user):
    """Kick off the batch job. Returns immediately with a task id to poll."""
    student = current_student(user)
    if not student.applications:
        return jsonify(message='You have no applications to export'), 400

    task = export_applications_csv.delay(student.id)
    return jsonify(message='Export started — you will be alerted when it is ready',
                   task_id=task.id), 202


@student_bp.get('/export/<task_id>')
@role_required('student')
def export_status(user, task_id):
    """Polled by the dashboard so it can raise the 'export ready' alert."""
    result = AsyncResult(task_id, app=celery)

    if result.successful():
        return jsonify(state='SUCCESS', filename=result.result)
    if result.failed():
        return jsonify(state='FAILURE', message='The export job failed'), 500
    return jsonify(state=result.state)


@student_bp.get('/export/download/<path:filename>')
@role_required('student')
def download_export(user, filename):
    student = current_student(user)

    # Filenames are namespaced by roll number — refuse anyone else's export.
    if not filename.startswith(f'applications_{student.roll_number or student.id}_'):
        return jsonify(message='That export is not yours'), 403

    return send_from_directory(
        current_app.config['EXPORT_FOLDER'],
        secure_filename(filename),
        as_attachment=True,
    )
