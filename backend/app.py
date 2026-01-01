import os
from datetime import timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from models import db, User, Student, Company, Job, Application, Announcement
from sqlalchemy import func, or_, and_
from werkzeug.utils import secure_filename
import openpyxl
from io import BytesIO

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
CORS(app)
jwt = JWTManager(app)

# Helper function to get user ID from JWT
def get_user_id():
    """Get user ID from JWT identity (convert string back to int)"""
    identity = get_jwt_identity()
    return int(identity) if isinstance(identity, str) else identity

# Register blueprints
from company_advanced_routes import company_bp
from admin_routes import admin_bp
app.register_blueprint(company_bp)
app.register_blueprint(admin_bp)

# ==================== Authentication Routes ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user (Student or Company)"""
    try:
        data = request.get_json()
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        user = User(
            email=data['email'],
            role_id=data['role_id'],  # 1=Student, 2=Company
            is_verified=False
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()
        
        # Create role-specific profile
        if data['role_id'] == 1:  # Student
            student = Student(
                user_id=user.id,
                full_name=data['full_name'],
                enrollment_number=data['enrollment_number'],
                branch=data['branch'],
                cgpa=data['cgpa'],
                graduation_year=data['graduation_year'],
                phone=data.get('phone', '')
            )
            db.session.add(student)
        
        elif data['role_id'] == 2:  # Company
            company = Company(
                user_id=user.id,
                company_name=data['company_name'],
                industry=data.get('industry', ''),
                hr_name=data['hr_name'],
                hr_phone=data.get('hr_phone', '')
            )
            db.session.add(company)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful. Please wait for admin verification.',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        if not user.is_verified and user.role_id != 3:
            return jsonify({'error': 'Account not verified by admin'}), 403
        
        # Generate JWT token
        access_token = create_access_token(identity=str(user.id))
        
        # Get profile data
        profile = None
        if user.role_id == 1:
            profile = user.student.to_dict() if user.student else None
        elif user.role_id == 2:
            profile = user.company.to_dict() if user.company else None
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict(),
            'profile': profile
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Student Routes ====================

@app.route('/api/student/profile', methods=['GET', 'PUT'])
@jwt_required()
def student_profile():
    """Get or update student profile"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        if request.method == 'GET':
            return jsonify(student.to_dict()), 200
        
        # PUT - Update profile
        data = request.get_json()
        student.full_name = data.get('full_name', student.full_name)
        student.phone = data.get('phone', student.phone)
        student.skills = data.get('skills', student.skills)
        student.resume_url = data.get('resume_url', student.resume_url)
        
        # Check profile completion
        if all([student.full_name, student.phone, student.resume_url, student.skills]):
            student.profile_completed = True
        
        db.session.commit()
        return jsonify(student.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/jobs', methods=['GET'])
@jwt_required()
def get_student_jobs():
    """Get jobs eligible for the student"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        # Get approved jobs that match student's eligibility
        jobs = Job.query.filter(
            Job.status == 'Approved',
            Job.min_cgpa <= student.cgpa,
            or_(
                Job.eligible_branches.like(f'%{student.branch}%'),
                Job.eligible_branches == None
            )
        ).order_by(Job.application_deadline.asc()).all()
        
        # Check which jobs student has already applied to
        applied_job_ids = [app.job_id for app in student.applications]
        
        jobs_data = []
        for job in jobs:
            job_dict = job.to_dict()
            job_dict['has_applied'] = job.id in applied_job_ids
            jobs_data.append(job_dict)
        
        return jsonify(jobs_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/apply/<int:job_id>', methods=['POST'])
@jwt_required()
def apply_to_job(job_id):
    """Apply to a job"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        # Check if profile is completed
        if not student.profile_completed:
            return jsonify({'error': 'Please complete your profile before applying'}), 400
        
        # Check if already applied
        existing = Application.query.filter_by(
            student_id=student.id,
            job_id=job_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Already applied to this job'}), 400
        
        # Create application
        application = Application(
            student_id=student.id,
            job_id=job_id,
            status='Applied'
        )
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'message': 'Application submitted successfully',
            'application': application.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/applications', methods=['GET'])
@jwt_required()
def get_student_applications():
    """Get all applications of the student"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        applications = user.student.applications
        return jsonify([app.to_dict() for app in applications]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Company Routes ====================

@app.route('/api/company/profile', methods=['GET', 'PUT'])
@jwt_required()
def company_profile():
    """Get or update company profile"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 2:
            return jsonify({'error': 'Unauthorized'}), 403
        
        company = user.company
        
        if request.method == 'GET':
            return jsonify(company.to_dict()), 200
        
        # PUT - Update profile
        data = request.get_json()
        company.company_name = data.get('company_name', company.company_name)
        company.industry = data.get('industry', company.industry)
        company.hr_name = data.get('hr_name', company.hr_name)
        company.hr_phone = data.get('hr_phone', company.hr_phone)
        company.company_website = data.get('company_website', company.company_website)
        company.logo_url = data.get('logo_url', company.logo_url)
        company.description = data.get('description', company.description)
        
        db.session.commit()
        return jsonify(company.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/company/jobs', methods=['GET', 'POST'])
@jwt_required()
def company_jobs():
    """Get all jobs posted by company or create new job"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 2:
            return jsonify({'error': 'Unauthorized'}), 403
        
        company = user.company
        
        if request.method == 'GET':
            jobs = company.jobs
            return jsonify([job.to_dict() for job in jobs]), 200
        
        # POST - Create new job
        data = request.get_json()
        job = Job(
            company_id=company.id,
            title=data['title'],
            job_type=data['job_type'],
            description=data['description'],
            requirements=data.get('requirements', ''),
            location=data.get('location', ''),
            salary_range=data.get('salary_range', ''),
            min_cgpa=data.get('min_cgpa', 0.0),
            eligible_branches=data.get('eligible_branches', ''),
            application_deadline=data['application_deadline'],
            status='Pending'  # Needs admin approval
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'message': 'Job posted successfully. Awaiting admin approval.',
            'job': job.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/company/job/<int:job_id>/applicants', methods=['GET'])
@jwt_required()
def get_job_applicants(job_id):
    """Get all applicants for a specific job"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 2:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Verify job belongs to this company
        job = Job.query.get(job_id)
        if not job or job.company_id != user.company.id:
            return jsonify({'error': 'Job not found'}), 404
        
        applications = Application.query.filter_by(job_id=job_id).all()
        
        applicants_data = []
        for app in applications:
            student_data = app.student.to_dict()
            student_data['application_status'] = app.status
            student_data['applied_at'] = app.applied_at.isoformat()
            student_data['application_id'] = app.id
            applicants_data.append(student_data)
        
        return jsonify(applicants_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/company/applicant-status', methods=['PUT'])
@jwt_required()
def update_applicant_status():
    """Update applicant status (Applied -> Shortlisted -> Interview -> Selected/Rejected)"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 2:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        application = Application.query.get(data['application_id'])
        
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        # Verify job belongs to this company
        if application.job.company_id != user.company.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        application.status = data['status']
        application.notes = data.get('notes', application.notes)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Application status updated',
            'application': application.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/company/export-applicants/<int:job_id>', methods=['GET'])
@jwt_required()
def export_applicants(job_id):
    """Export applicants to Excel"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 2:
            return jsonify({'error': 'Unauthorized'}), 403
        
        job = Job.query.get(job_id)
        if not job or job.company_id != user.company.id:
            return jsonify({'error': 'Job not found'}), 404
        
        applications = Application.query.filter_by(job_id=job_id).all()
        
        # Create Excel workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Applicants"
        
        # Headers
        headers = ['Name', 'Enrollment No', 'Branch', 'CGPA', 'Phone', 'Email', 'Status', 'Applied Date']
        ws.append(headers)
        
        # Data
        for app in applications:
            student = app.student
            ws.append([
                student.full_name,
                student.enrollment_number,
                student.branch,
                float(student.cgpa),
                student.phone,
                student.user.email,
                app.status,
                app.applied_at.strftime('%Y-%m-%d')
            ])
        
        # Save to bytes
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return jsonify({
            'message': 'Export ready',
            'filename': f'applicants_{job_id}.xlsx'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Admin Routes ====================

@app.route('/api/admin/pending-users', methods=['GET'])
@jwt_required()
def get_pending_users():
    """Get all unverified users"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 3:
            return jsonify({'error': 'Unauthorized'}), 403
        
        users = User.query.filter_by(is_verified=False).all()
        
        users_data = []
        for u in users:
            user_dict = u.to_dict()
            if u.role_id == 1:
                user_dict['profile'] = u.student.to_dict() if u.student else None
            elif u.role_id == 2:
                user_dict['profile'] = u.company.to_dict() if u.company else None
            users_data.append(user_dict)
        
        return jsonify(users_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/verify-user/<int:user_id>', methods=['PUT'])
@jwt_required()
def verify_user(user_id):
    """Verify a user account"""
    try:
        admin_id = get_user_id()
        admin = User.query.get(admin_id)
        
        if admin.role_id != 3:
            return jsonify({'error': 'Unauthorized'}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_verified = True
        db.session.commit()
        
        return jsonify({'message': 'User verified successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/pending-jobs', methods=['GET'])
@jwt_required()
def get_pending_jobs():
    """Get all jobs pending approval"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 3:
            return jsonify({'error': 'Unauthorized'}), 403
        
        jobs = Job.query.filter_by(status='Pending').all()
        return jsonify([job.to_dict() for job in jobs]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/approve-job/<int:job_id>', methods=['PUT'])
@jwt_required()
def approve_job(job_id):
    """Approve or reject a job posting"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 3:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        job = Job.query.get(job_id)
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        job.status = data['status']  # 'Approved' or 'Rejected'
        db.session.commit()
        
        return jsonify({
            'message': f'Job {data["status"].lower()} successfully',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Get placement statistics and analytics"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 3:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Overall statistics
        total_students = Student.query.count()
        total_companies = Company.query.filter_by().join(User).filter(User.is_verified == True).count()
        total_jobs = Job.query.filter_by(status='Approved').count()
        
        # Placement statistics
        placed_students = db.session.query(func.count(func.distinct(Application.student_id))).filter(
            Application.status == 'Selected'
        ).scalar()
        
        # Branch-wise statistics
        branch_data = []
        branches = db.session.query(Student.branch).distinct().all()
        for (branch,) in branches:
            total = Student.query.filter_by(branch=branch).count()
            placed = db.session.query(func.count(func.distinct(Application.student_id))).filter(
                Student.branch == branch,
                Application.status == 'Selected'
            ).join(Student).scalar() or 0
            branch_data.append({
                'branch': branch,
                'total': total,
                'placed': placed,
                'percentage': round(placed * 100 / total, 2) if total > 0 else 0
            })
        
        # Job type distribution
        job_type_stats = db.session.query(
            Job.job_type,
            func.count(Job.id)
        ).filter(Job.status == 'Approved').group_by(Job.job_type).all()
        
        analytics = {
            'overall': {
                'total_students': total_students,
                'placed_students': placed_students or 0,
                'placement_percentage': round((placed_students or 0) * 100 / total_students, 2) if total_students > 0 else 0,
                'total_companies': total_companies,
                'total_jobs': total_jobs
            },
            'branch_wise': branch_data,
            'job_types': [{'type': jt, 'count': count} for jt, count in job_type_stats]
        }
        
        return jsonify(analytics), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/announcements', methods=['GET', 'POST'])
@jwt_required()
def announcements():
    """Get all announcements or create new one"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 3:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if request.method == 'GET':
            announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
            return jsonify([ann.to_dict() for ann in announcements]), 200
        
        # POST - Create announcement
        data = request.get_json()
        announcement = Announcement(
            title=data['title'],
            message=data['message'],
            target_role=data.get('target_role'),  # 1=Student, 2=Company, None=All
            created_by=user_id
        )
        db.session.add(announcement)
        db.session.commit()
        
        return jsonify({
            'message': 'Announcement created successfully',
            'announcement': announcement.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/announcements', methods=['GET'])
@jwt_required()
def get_announcements():
    """Get announcements for the current user's role"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        # Get announcements for this role or all roles
        announcements = Announcement.query.filter(
            or_(
                Announcement.target_role == user.role_id,
                Announcement.target_role == None
            )
        ).order_by(Announcement.created_at.desc()).limit(10).all()
        
        return jsonify([ann.to_dict() for ann in announcements]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Health Check ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Placement Portal API is running'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

