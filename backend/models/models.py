from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class User(db.Model):
    """Unified user model — one table for all three roles."""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)     # admin | company | student
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class CompanyProfile(db.Model):
    __tablename__ = 'company_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    company_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(120))
    location = db.Column(db.String(120))
    hr_contact = db.Column(db.String(120))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    approval_status = db.Column(db.String(20), default='pending', nullable=False)  # pending|approved|rejected
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('company_profile', uselist=False))
    drives = db.relationship('PlacementDrive', backref='company',
                             lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'industry': self.industry,
            'location': self.location,
            'hr_contact': self.hr_contact,
            'website': self.website,
            'description': self.description,
            'approval_status': self.approval_status,
            'is_blacklisted': self.is_blacklisted,
            'email': self.user.email,
            'is_active': self.user.is_active,
            'drive_count': len(self.drives),
        }


class StudentProfile(db.Model):
    __tablename__ = 'student_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    name = db.Column(db.String(120), nullable=False)
    roll_number = db.Column(db.String(50), unique=True)
    branch = db.Column(db.String(80))
    cgpa = db.Column(db.Float, default=0.0)
    year = db.Column(db.Integer, default=1)
    skills = db.Column(db.String(300))          # comma-separated
    resume_path = db.Column(db.String(300))
    is_blacklisted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    applications = db.relationship('Application', backref='student',
                                   lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'roll_number': self.roll_number,
            'branch': self.branch,
            'cgpa': self.cgpa,
            'year': self.year,
            'skills': self.skills,
            'resume_path': self.resume_path,
            'is_blacklisted': self.is_blacklisted,
            'email': self.user.email,
            'is_active': self.user.is_active,
        }


class PlacementDrive(db.Model):
    __tablename__ = 'placement_drive'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    drive_name = db.Column(db.String(200), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    job_description = db.Column(db.Text)
    skills_required = db.Column(db.String(300))     # comma-separated
    experience_required = db.Column(db.String(80))  # e.g. "0-1 years", "Freshers"
    benefits = db.Column(db.String(300))
    # Eligibility criteria
    eligible_branches = db.Column(db.String(300))   # comma separated, or "All"
    min_cgpa = db.Column(db.Float, default=0.0)
    eligible_year = db.Column(db.Integer, default=4)
    salary = db.Column(db.Float, default=0.0)
    location = db.Column(db.String(120))
    deadline = db.Column(db.DateTime, nullable=False)
    # pending | approved | rejected | closed | cancelled
    status = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='drive',
                                   lazy=True, cascade='all, delete-orphan')

    def is_open(self):
        return self.status == 'approved' and self.deadline >= datetime.utcnow()

    def check_eligibility(self, student):
        """Return None if eligible, else a human-readable reason."""
        if student.cgpa < self.min_cgpa:
            return f'Requires a minimum CGPA of {self.min_cgpa} (yours is {student.cgpa})'
        if student.year != self.eligible_year:
            return f'Open to year {self.eligible_year} students only'
        if self.eligible_branches:
            allowed = [b.strip().lower() for b in self.eligible_branches.split(',')]
            if 'all' not in allowed and (student.branch or '').lower() not in allowed:
                return f'Open to these branches only: {self.eligible_branches}'
        return None

    def to_dict(self, student=None):
        data = {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company.company_name,
            'drive_name': self.drive_name,
            'job_title': self.job_title,
            'job_description': self.job_description,
            'skills_required': self.skills_required,
            'experience_required': self.experience_required,
            'benefits': self.benefits,
            'eligible_branches': self.eligible_branches,
            'min_cgpa': self.min_cgpa,
            'eligible_year': self.eligible_year,
            'salary': self.salary,
            'location': self.location,
            'deadline': self.deadline.isoformat(),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'applicant_count': len(self.applications),
        }
        if student is not None:
            reason = self.check_eligibility(student)
            data['eligible'] = reason is None
            data['ineligible_reason'] = reason
            data['already_applied'] = any(a.student_id == student.id for a in self.applications)
        return data


class Application(db.Model):
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    # applied | shortlisted | waiting | selected | rejected
    status = db.Column(db.String(20), default='applied', nullable=False)
    placement = db.relationship('Placement', backref='application', uselist=False,
                                cascade='all, delete-orphan')
    interview_mode = db.Column(db.String(50), default='In-person')
    interview_date = db.Column(db.DateTime)
    remark = db.Column(db.String(300), default='None')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # A student may apply to a given drive exactly once.
    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='uq_student_drive'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'roll_number': self.student.roll_number,
            'branch': self.student.branch,
            'cgpa': self.student.cgpa,
            'resume_path': self.student.resume_path,
            'drive_id': self.drive_id,
            'drive_name': self.drive.drive_name,
            'job_title': self.drive.job_title,
            'company_name': self.drive.company.company_name,
            'application_date': self.application_date.isoformat(),
            'deadline': self.drive.deadline.isoformat(),
            'status': self.status,
            'interview_mode': self.interview_mode,
            'interview_date': self.interview_date.isoformat() if self.interview_date else None,
            'remark': self.remark,
            'placement': self.placement.to_dict() if self.placement else None,
        }


class Placement(db.Model):
    """A confirmed placement, created once an Application is marked 'selected'."""
    __tablename__ = 'placement'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'),
                               nullable=False, unique=True)
    position = db.Column(db.String(200))
    salary = db.Column(db.Float, default=0.0)
    joining_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('StudentProfile')
    company = db.relationship('CompanyProfile')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name,
            'company_id': self.company_id,
            'company_name': self.company.company_name,
            'position': self.position,
            'salary': self.salary,
            'joining_date': self.joining_date.isoformat() if self.joining_date else None,
            'created_at': self.created_at.isoformat(),
        }
