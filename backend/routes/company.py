"""Company endpoints — profile, drives, and applicant management."""
import os
from datetime import datetime

from flask import Blueprint, request, jsonify, send_from_directory, current_app

from extensions import db, cache
from models import PlacementDrive, Application, Placement
from security import role_required, current_company

company_bp = Blueprint('company', __name__, url_prefix='/api/company')

VALID_STATUSES = ('applied', 'shortlisted', 'waiting', 'selected', 'rejected')


def _owned_drive_or_error(company, did):
    """Fetch a drive, ensuring it belongs to this company."""
    drive = PlacementDrive.query.get_or_404(did)
    if drive.company_id != company.id:
        return None, (jsonify(message='That drive does not belong to you'), 403)
    return drive, None


# ── Profile / dashboard ───────────────────────────────────────────────

@company_bp.get('/profile')
@role_required('company')
def get_profile(user):
    company = current_company(user)
    if not company:
        return jsonify(message='Company profile not found'), 404
    return jsonify(company.to_dict())


@company_bp.put('/profile')
@role_required('company')
def update_profile(user):
    company = current_company(user)
    data = request.get_json() or {}

    company.company_name = data.get('company_name', company.company_name)
    company.industry = data.get('industry', company.industry)
    company.location = data.get('location', company.location)
    company.hr_contact = data.get('hr_contact', company.hr_contact)
    company.website = data.get('website', company.website)
    company.description = data.get('description', company.description)

    db.session.commit()
    return jsonify(message='Profile updated', company=company.to_dict())


# ── Drives ────────────────────────────────────────────────────────────

@company_bp.get('/drives')
@role_required('company')
def list_drives(user):
    """Split into upcoming vs closed, matching the company dashboard wireframe."""
    company = current_company(user)
    drives = [d.to_dict() for d in company.drives]

    upcoming = [d for d in drives if d['status'] in ('pending', 'approved')]
    closed = [d for d in drives if d['status'] in ('closed', 'rejected', 'cancelled')]
    return jsonify(upcoming=upcoming, closed=closed)


@company_bp.post('/drives')
@role_required('company')
def create_drive(user):
    company = current_company(user)

    # A drive may only be created once the admin has approved the company.
    if company.approval_status != 'approved':
        return jsonify(message='Your company is not approved by the admin yet'), 403
    if company.is_blacklisted:
        return jsonify(message='Blacklisted companies cannot create drives'), 403

    data = request.get_json() or {}
    for field in ('drive_name', 'job_title', 'deadline'):
        if not (data.get(field) or '').strip():
            return jsonify(message=f'"{field}" is required'), 400

    try:
        deadline = datetime.fromisoformat(data['deadline'])
    except ValueError:
        return jsonify(message='Deadline must be a valid date'), 400
    if deadline < datetime.utcnow():
        return jsonify(message='Deadline cannot be in the past'), 400

    drive = PlacementDrive(
        company_id=company.id,
        drive_name=data['drive_name'].strip(),
        job_title=data['job_title'].strip(),
        job_description=data.get('job_description', ''),
        skills_required=data.get('skills_required', ''),
        experience_required=data.get('experience_required', ''),
        benefits=data.get('benefits', ''),
        eligible_branches=data.get('eligible_branches', 'All'),
        min_cgpa=float(data.get('min_cgpa') or 0),
        eligible_year=int(data.get('eligible_year') or 4),
        salary=float(data.get('salary') or 0),
        location=data.get('location', ''),
        deadline=deadline,
    )
    db.session.add(drive)
    db.session.commit()

    cache.delete('admin_stats')
    return jsonify(message='Drive created — awaiting admin approval',
                   drive=drive.to_dict()), 201


@company_bp.get('/drives/<int:did>')
@role_required('company')
def get_drive(user, did):
    drive, err = _owned_drive_or_error(current_company(user), did)
    if err:
        return err
    return jsonify(drive.to_dict())


@company_bp.put('/drives/<int:did>/complete')
@role_required('company')
def complete_drive(user, did):
    """'Mark as complete' from the wireframe — moves the drive to Closed."""
    drive, err = _owned_drive_or_error(current_company(user), did)
    if err:
        return err

    drive.status = 'closed'
    db.session.commit()
    cache.delete('admin_stats')
    cache.delete('open_drives')
    return jsonify(message=f'"{drive.drive_name}" marked as complete')


# ── Applications for a drive ──────────────────────────────────────────

@company_bp.get('/drives/<int:did>/applications')
@role_required('company')
def drive_applications(user, did):
    drive, err = _owned_drive_or_error(current_company(user), did)
    if err:
        return err
    return jsonify([a.to_dict() for a in drive.applications])


@company_bp.get('/applications/<int:aid>')
@role_required('company')
def get_application(user, aid):
    company = current_company(user)
    application = Application.query.get_or_404(aid)

    if application.drive.company_id != company.id:
        return jsonify(message='That application is not for one of your drives'), 403
    return jsonify(application.to_dict())


@company_bp.put('/applications/<int:aid>')
@role_required('company')
def update_application(user, aid):
    """Shortlist / mark waiting / reject / select an applicant."""
    company = current_company(user)
    application = Application.query.get_or_404(aid)

    if application.drive.company_id != company.id:
        return jsonify(message='That application is not for one of your drives'), 403

    data = request.get_json() or {}
    status = data.get('status')
    if status not in VALID_STATUSES:
        return jsonify(message=f'Status must be one of: {", ".join(VALID_STATUSES)}'), 400

    application.status = status
    application.interview_mode = data.get('interview_mode', application.interview_mode)
    if data.get('interview_date'):
        application.interview_date = datetime.fromisoformat(data['interview_date'])
    application.remark = data.get('remark', application.remark)

    # Selecting a candidate records a Placement (position/salary/joining date).
    if status == 'selected' and not application.placement:
        joining_date = data.get('joining_date')
        db.session.add(Placement(
            student_id=application.student_id,
            company_id=company.id,
            application_id=application.id,
            position=data.get('position', application.drive.job_title),
            salary=float(data.get('salary') or application.drive.salary or 0),
            joining_date=datetime.fromisoformat(joining_date) if joining_date else None,
        ))

    db.session.commit()
    return jsonify(message='Application updated', application=application.to_dict())


@company_bp.get('/resume/<int:aid>')
@role_required('company')
def view_resume(user, aid):
    """Serve an applicant's resume — only for the company running that drive."""
    company = current_company(user)
    application = Application.query.get_or_404(aid)

    if application.drive.company_id != company.id:
        return jsonify(message='Not your applicant'), 403
    if not application.student.resume_path:
        return jsonify(message='This student has not uploaded a resume'), 404

    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        application.student.resume_path,
    )
