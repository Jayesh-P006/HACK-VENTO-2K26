from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.SmallInteger, nullable=False)  # 1=Student, 2=Company, 3=Admin
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    company = db.relationship('Company', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role_id': self.role_id,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat()
        }


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    enrollment_number = db.Column(db.String(50), unique=True, nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    cgpa = db.Column(db.Numeric(3, 2), nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(15))
    resume_url = db.Column(db.String(500))
    skills = db.Column(db.Text)
    profile_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='student', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'enrollment_number': self.enrollment_number,
            'branch': self.branch,
            'cgpa': float(self.cgpa),
            'graduation_year': self.graduation_year,
            'phone': self.phone,
            'resume_url': self.resume_url,
            'skills': self.skills,
            'profile_completed': self.profile_completed
        }


class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(100))
    hr_name = db.Column(db.String(255), nullable=False)
    hr_phone = db.Column(db.String(15))
    company_website = db.Column(db.String(255))
    logo_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='company', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_name': self.company_name,
            'industry': self.industry,
            'hr_name': self.hr_name,
            'hr_phone': self.hr_phone,
            'company_website': self.company_website,
            'logo_url': self.logo_url,
            'description': self.description
        }


class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    job_type = db.Column(db.Enum('Internship', 'Full-Time', 'Part-Time'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    location = db.Column(db.String(255))
    salary_range = db.Column(db.String(100))
    min_cgpa = db.Column(db.Numeric(3, 2), default=0.00)
    eligible_branches = db.Column(db.Text)  # JSON-like format: ["CSE", "IT", "ECE"]
    min_10th_percentage = db.Column(db.Numeric(5, 2))
    min_12th_percentage = db.Column(db.Numeric(5, 2))
    application_deadline = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('Pending', 'Approved', 'Rejected', 'Closed'), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='job', cascade='all, delete-orphan')
    hiring_rounds = db.relationship('HiringRound', backref='job', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company.company_name if self.company else None,
            'company_logo': self.company.logo_url if self.company else None,
            'title': self.title,
            'job_type': self.job_type,
            'description': self.description,
            'requirements': self.requirements,
            'location': self.location,
            'salary_range': self.salary_range,
            'min_cgpa': float(self.min_cgpa),
            'eligible_branches': self.eligible_branches,
            'min_10th_percentage': float(self.min_10th_percentage) if self.min_10th_percentage else None,
            'min_12th_percentage': float(self.min_12th_percentage) if self.min_12th_percentage else None,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    status = db.Column(db.Enum('Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected'), default='Applied')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    
    __table_args__ = (db.UniqueConstraint('student_id', 'job_id', name='unique_application'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'job_id': self.job_id,
            'job_title': self.job.title if self.job else None,
            'company_name': self.job.company.company_name if self.job and self.job.company else None,
            'status': self.status,
            'applied_at': self.applied_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'notes': self.notes
        }


class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    target_role = db.Column(db.SmallInteger)  # 1=Student, 2=Company, NULL=All
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'target_role': self.target_role,
            'created_at': self.created_at.isoformat()
        }


class HiringRound(db.Model):
    """Represents each round in the hiring process (Aptitude, GD, Tech Interview, HR)"""
    __tablename__ = 'hiring_rounds'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)  # 1=Aptitude, 2=GD, 3=Tech, 4=HR
    round_type = db.Column(db.String(50), nullable=False)  # Aptitude, GD, Tech Interview, HR
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications_rounds = db.relationship('ApplicationRound', backref='hiring_round', cascade='all, delete-orphan')
    interview_slots = db.relationship('InterviewSlot', backref='hiring_round', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'round_number': self.round_number,
            'round_type': self.round_type,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'created_at': self.created_at.isoformat()
        }


class ApplicationRound(db.Model):
    """Track student's progress through each hiring round"""
    __tablename__ = 'application_rounds'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    hiring_round_id = db.Column(db.Integer, db.ForeignKey('hiring_rounds.id'), nullable=False)
    status = db.Column(db.Enum('Pending', 'Scheduled', 'Completed', 'Passed', 'Failed'), default='Pending')
    score = db.Column(db.Numeric(5, 2))
    feedback = db.Column(db.Text)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    application = db.relationship('Application', backref='round_progresses')
    
    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'hiring_round_id': self.hiring_round_id,
            'status': self.status,
            'score': float(self.score) if self.score else None,
            'feedback': self.feedback,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class InterviewSlot(db.Model):
    """Interview scheduling system"""
    __tablename__ = 'interview_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    hiring_round_id = db.Column(db.Integer, db.ForeignKey('hiring_rounds.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    slot_date = db.Column(db.Date, nullable=False)
    slot_time = db.Column(db.Time, nullable=False)
    interviewer_name = db.Column(db.String(255))
    interviewer_email = db.Column(db.String(255))
    meeting_link = db.Column(db.String(500))  # For online interviews
    location = db.Column(db.String(255))  # For onsite interviews
    max_capacity = db.Column(db.Integer, default=1)
    current_bookings = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum('Available', 'Full', 'Completed', 'Cancelled'), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('InterviewBooking', backref='slot', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'hiring_round_id': self.hiring_round_id,
            'slot_date': self.slot_date.isoformat(),
            'slot_time': str(self.slot_time),
            'interviewer_name': self.interviewer_name,
            'meeting_link': self.meeting_link,
            'location': self.location,
            'max_capacity': self.max_capacity,
            'current_bookings': self.current_bookings,
            'status': self.status
        }


class InterviewBooking(db.Model):
    """Student booking an interview slot"""
    __tablename__ = 'interview_bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    interview_slot_id = db.Column(db.Integer, db.ForeignKey('interview_slots.id'), nullable=False)
    application_round_id = db.Column(db.Integer, db.ForeignKey('application_rounds.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    status = db.Column(db.Enum('Confirmed', 'No-Show', 'Rescheduled', 'Completed'), default='Confirmed')
    booking_notes = db.Column(db.Text)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    application_round = db.relationship('ApplicationRound', backref='interview_bookings')
    student = db.relationship('Student', backref='interview_bookings')
    
    def to_dict(self):
        return {
            'id': self.id,
            'interview_slot_id': self.interview_slot_id,
            'student_id': self.student_id,
            'status': self.status,
            'booked_at': self.booked_at.isoformat()
        }


class OfferLetter(db.Model):
    """Digital offer letter management"""
    __tablename__ = 'offer_letters'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Offer details
    designation = db.Column(db.String(255), nullable=False)
    ctc = db.Column(db.String(100), nullable=False)
    annual_ctc = db.Column(db.Numeric(12, 2))
    job_location = db.Column(db.String(255))
    joining_date = db.Column(db.Date)
    notice_period = db.Column(db.Integer)  # Days
    
    # Letter content
    offer_content = db.Column(db.Text, nullable=False)
    template_used = db.Column(db.String(255))
    
    # Status tracking
    status = db.Column(db.Enum('Generated', 'Sent', 'Accepted', 'Rejected', 'Expired'), default='Generated')
    sent_date = db.Column(db.DateTime)
    acceptance_date = db.Column(db.DateTime)
    expiry_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = db.relationship('Application', backref='offer_letters')
    company = db.relationship('Company', backref='offer_letters')
    student = db.relationship('Student', backref='offer_letters')
    
    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'designation': self.designation,
            'ctc': self.ctc,
            'annual_ctc': float(self.annual_ctc) if self.annual_ctc else None,
            'job_location': self.job_location,
            'joining_date': self.joining_date.isoformat() if self.joining_date else None,
            'status': self.status,
            'sent_date': self.sent_date.isoformat() if self.sent_date else None,
            'acceptance_date': self.acceptance_date.isoformat() if self.acceptance_date else None,
            'created_at': self.created_at.isoformat()
        }


# ==================== ADMIN DASHBOARD MODELS ====================

class StudentVerification(db.Model):
    """Document verification queue for newly registered students"""
    __tablename__ = 'student_verification'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    status = db.Column(db.Enum('Pending', 'Verified', 'Rejected'), default='Pending')
    
    # Document details
    marksheet_10th_url = db.Column(db.String(500))
    marksheet_12th_url = db.Column(db.String(500))
    degree_certificate_url = db.Column(db.String(500))
    verification_date = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Admin who verified
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='verification_record')
    admin = db.relationship('User', backref='verified_students')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'enrollment_number': self.student.enrollment_number if self.student else None,
            'branch': self.student.branch if self.student else None,
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'submitted_at': self.submitted_at.isoformat(),
            'verification_date': self.verification_date.isoformat() if self.verification_date else None
        }


class StudentBlacklist(db.Model):
    """Student account blacklist for disciplinary action"""
    __tablename__ = 'student_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), unique=True, nullable=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    reason = db.Column(db.Text, nullable=False)
    severity = db.Column(db.Enum('Low', 'Medium', 'High', 'Critical'), default='Medium')
    
    blacklisted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blacklisted_date = db.Column(db.DateTime, default=datetime.utcnow)
    unblacklist_date = db.Column(db.DateTime)  # For temporary blacklisting
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='blacklist_record')
    admin = db.relationship('User', backref='blacklisted_students')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'is_blacklisted': self.is_blacklisted,
            'reason': self.reason,
            'severity': self.severity,
            'blacklisted_date': self.blacklisted_date.isoformat(),
            'unblacklist_date': self.unblacklist_date.isoformat() if self.unblacklist_date else None
        }


class Department(db.Model):
    """Master list of departments/branches"""
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    total_students = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'total_students': self.total_students,
            'is_active': self.is_active
        }


class BatchYear(db.Model):
    """Master list of batch/graduation years"""
    __tablename__ = 'batch_years'
    
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False)
    academic_session = db.Column(db.String(20), nullable=False)  # e.g., "2023-2024"
    total_students = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'year': self.year,
            'academic_session': self.academic_session,
            'total_students': self.total_students,
            'is_active': self.is_active
        }


class Skill(db.Model):
    """Master list of technical skills"""
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g., "Programming", "Framework", "Database"
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'is_active': self.is_active
        }


class PlacementStats(db.Model):
    """Aggregated placement statistics for analytics dashboard"""
    __tablename__ = 'placement_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    
    # Overall stats
    total_students = db.Column(db.Integer, default=0)
    placed_students = db.Column(db.Integer, default=0)
    unplaced_students = db.Column(db.Integer, default=0)
    highest_package = db.Column(db.Numeric(12, 2), default=0)
    average_package = db.Column(db.Numeric(12, 2), default=0)
    
    # Department-wise
    department_stats = db.Column(db.JSON)  # {"CSE": {"placed": 50, "total": 80}, ...}
    
    # Company visits
    total_companies_visiting = db.Column(db.Integer, default=0)
    companies_in_interview = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'total_students': self.total_students,
            'placed_students': self.placed_students,
            'unplaced_students': self.unplaced_students,
            'highest_package': float(self.highest_package) if self.highest_package else 0,
            'average_package': float(self.average_package) if self.average_package else 0,
            'department_stats': self.department_stats,
            'total_companies_visiting': self.total_companies_visiting,
            'companies_in_interview': self.companies_in_interview
        }


class CompanyVisit(db.Model):
    """Track company visits and their current status"""
    __tablename__ = 'company_visits'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    
    status = db.Column(db.Enum('Scheduled', 'Interview Stage', 'Offer Stage', 'Completed', 'Cancelled'), default='Scheduled')
    location = db.Column(db.String(255))
    interview_type = db.Column(db.Enum('Online', 'Onsite', 'Hybrid'), default='Online')
    
    total_applications = db.Column(db.Integer, default=0)
    shortlisted_count = db.Column(db.Integer, default=0)
    selected_count = db.Column(db.Integer, default=0)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = db.relationship('Job', backref='visits')
    company = db.relationship('Company', backref='visits')
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company.company_name if self.company else None,
            'company_logo': self.company.logo_url if self.company else None,
            'job_title': self.job.title if self.job else None,
            'visit_date': self.visit_date.isoformat(),
            'status': self.status,
            'location': self.location,
            'interview_type': self.interview_type,
            'total_applications': self.total_applications,
            'shortlisted_count': self.shortlisted_count,
            'selected_count': self.selected_count
        }
