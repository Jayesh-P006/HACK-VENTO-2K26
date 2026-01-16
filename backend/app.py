import os
from datetime import timedelta, datetime
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
from models import db, User, Student, Company, Job, Application, Announcement, StudentVerification, Skill
from otp_service import generate_otp, send_otp_email, is_otp_valid, send_approval_pending_email
from models import HiringRound, ApplicationRound, OfferLetter, Batch, Admin, AdminVerification, AdminAccessLog, Department
from sqlalchemy import func, or_, and_, text
import openpyxl
from io import BytesIO
from werkzeug.exceptions import HTTPException
from sqlalchemy import inspect

# Load environment variables from the backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

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
CORS(app, resources={
    r"/*": {
        "origins": ["*", "https://hack-vento-2-k26-toer.vercel.app", "http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False,
        "max_age": 3600
    }
})
jwt = JWTManager(app)

# Initialize email service
from email_service import init_mail
init_mail(app)



def _maybe_init_database():
    """Create tables (and demo users) if database is empty.

    This is primarily for hosted environments like Railway where the MySQL
    database starts empty and interactive shell access may be limited.
    """
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            has_users_table = inspector.has_table('users')
            has_departments = inspector.has_table('departments')
            has_batches = inspector.has_table('batches')

            if not has_users_table or not has_departments or not has_batches:
                print('[db] core tables missing; creating all tables...')
                db.create_all()

            def ensure_otp_columns(table_name):
                if not inspector.has_table(table_name):
                    return
                existing_cols = {col['name'] for col in inspector.get_columns(table_name)}
                columns_to_add = []
                if 'otp' not in existing_cols:
                    columns_to_add.append("ADD COLUMN otp VARCHAR(6)")
                if 'otp_verified' not in existing_cols:
                    columns_to_add.append("ADD COLUMN otp_verified BOOLEAN DEFAULT FALSE")
                if 'otp_sent_at' not in existing_cols:
                    columns_to_add.append("ADD COLUMN otp_sent_at DATETIME")
                if 'otp_verified_at' not in existing_cols:
                    columns_to_add.append("ADD COLUMN otp_verified_at DATETIME")
                if 'otp_attempts' not in existing_cols:
                    columns_to_add.append("ADD COLUMN otp_attempts INT DEFAULT 0")

                for column_sql in columns_to_add:
                    print(f"[db] Adding {table_name} column: {column_sql}")
                    db.session.execute(text(f"ALTER TABLE {table_name} {column_sql}"))
                if columns_to_add:
                    db.session.commit()

            # Seed master data (departments, batches, skills)
            if not has_departments or Department.query.count() == 0:
                print('[db] seeding departments...')
                branches = [
                    {'name': 'CSE', 'full_name': 'Computer Science and Engineering'},
                    {'name': 'IT', 'full_name': 'Information Technology'},
                    {'name': 'ECE', 'full_name': 'Electronics and Communication Engineering'},
                    {'name': 'EEE', 'full_name': 'Electrical and Electronics Engineering'},
                    {'name': 'ME', 'full_name': 'Mechanical Engineering'},
                    {'name': 'CE', 'full_name': 'Civil Engineering'},
                    {'name': 'Chemical', 'full_name': 'Chemical Engineering'},
                ]
                for branch in branches:
                    if not Department.query.filter_by(name=branch['name']).first():
                        db.session.add(Department(name=branch['name'], code=branch['name'][:3].upper(), description=branch['full_name']))
                db.session.commit()

            if not has_batches or Batch.query.count() == 0:
                print('[db] seeding batches...')
                batches_data = [
                    {'batch_code': '2023-27', 'start_year': 2023, 'end_year': 2027, 'degree': 'B.Tech', 'program': 'All', 'status': 'Active'},
                    {'batch_code': '2022-26', 'start_year': 2022, 'end_year': 2026, 'degree': 'B.Tech', 'program': 'All', 'status': 'Active'},
                    {'batch_code': '2021-25', 'start_year': 2021, 'end_year': 2025, 'degree': 'B.Tech', 'program': 'All', 'status': 'Active'},
                    {'batch_code': '2020-24', 'start_year': 2020, 'end_year': 2024, 'degree': 'B.Tech', 'program': 'All', 'status': 'Graduated'},
                ]
                for batch_data in batches_data:
                    if not Batch.query.filter_by(batch_code=batch_data['batch_code']).first():
                        db.session.add(Batch(**batch_data))
                db.session.commit()

            # Ensure OTP columns exist for verification tables
            ensure_otp_columns('student_verification')
            ensure_otp_columns('admin_verification')

            seed = os.getenv('SEED_DEMO_USERS', '1').strip().lower() in ('1', 'true', 'yes', 'y', 'on')
            if not seed:
                return

            # Seed demo users only if there are no users yet.
            if has_users_table and User.query.count() > 0:
                return

            print('[db] seeding demo users...')
            demo_accounts = [
                ('admin@university.edu', 'admin123', 3),
                ('student@university.edu', 'student123', 1),
                ('company@tech.com', 'company123', 2),
            ]

            for email, password, role_id in demo_accounts:
                existing = User.query.filter_by(email=email).first()
                if existing:
                    continue
                user = User(email=email, role_id=role_id, is_verified=True)
                db.session.add(user)
                db.session.flush()  # Get user.id
                
                # Create role-specific profiles
                if role_id == 1:  # Student
                    from models import Student
                    student = Student(
                        user_id=user.id,
                        full_name='Demo Student',
                        enrollment_number='DEMO2026001',
                        branch='CSE',
                        cgpa=8.5,
                        graduation_year=2026,
                        current_year=3,
                        phone='9999999999'
                    )
                    db.session.add(student)
                elif role_id == 2:  # Company
                    from models import Company
                    company = Company(
                        user_id=user.id,
                        company_name='Demo Tech Corp',
                        industry='Technology',
                        hr_name='Demo HR',
                        hr_phone='8888888888'
                    )
                    db.session.add(company)
                    
            db.session.commit()
            print('[db] demo users ready')
    except Exception as e:
        # Don't block app startup; surface in logs.
        try:
            db.session.rollback()
        except Exception:
            pass
        print('[db] init skipped/failed:', str(e))


def _normalize_skills(skills_text):
    if not skills_text:
        return []
    raw = [s.strip() for s in skills_text.replace('\n', ',').replace(';', ',').split(',')]
    cleaned = [s for s in raw if s]
    # Deduplicate case-insensitively, preserve original casing for first occurrence
    seen = set()
    result = []
    for s in cleaned:
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(s)
    return result


def _sync_skill_master_from_student(skills_text):
    """Ensure master Skill entries exist for all skills in the student profile."""
    try:
        for skill_name in _normalize_skills(skills_text):
            existing = Skill.query.filter(func.lower(Skill.name) == skill_name.lower()).first()
            if existing:
                continue
            skill = Skill(name=skill_name, category='Other', description='', is_active=True)
            db.session.add(skill)
        db.session.commit()
    except Exception:
        db.session.rollback()


def _fix_existing_demo_accounts():
    """Fix existing demo accounts that don't have student/company profiles"""
    try:
        with app.app_context():
            fixed_any = False
            
            # Fix student account
            student_user = User.query.filter_by(email='student@university.edu').first()
            if student_user and not student_user.student:
                print('[db] Fixing student profile for student@university.edu...')
                from models import Student
                student = Student(
                    user_id=student_user.id,
                    full_name='Demo Student',
                    enrollment_number='DEMO2026001',
                    branch='CSE',
                    cgpa=8.5,
                    graduation_year=2026,
                    current_year=3,
                    phone='9999999999'
                )
                db.session.add(student)
                fixed_any = True
            
            # Fix company account
            company_user = User.query.filter_by(email='company@tech.com').first()
            if company_user and not company_user.company:
                print('[db] Fixing company profile for company@tech.com...')
                from models import Company
                company = Company(
                    user_id=company_user.id,
                    company_name='Demo Tech Corp',
                    industry='Technology',
                    hr_name='Demo HR',
                    hr_phone='8888888888'
                )
                db.session.add(company)
                fixed_any = True
            
            if fixed_any:
                db.session.commit()
                print('[db] Demo account profiles fixed')
    except Exception as e:
        try:
            db.session.rollback()
        except Exception:
            pass
        print('[db] fix demo accounts failed:', str(e))


# Run DB init on startup (safe/idempotent)
_maybe_init_database()
_fix_existing_demo_accounts()

# Helper function to get user ID from JWT
def get_user_id():
    """Get user ID from JWT identity (convert string back to int)"""
    identity = get_jwt_identity()
    return int(identity) if isinstance(identity, str) else identity


def serialize_application(app):
    """Serialize an application with dynamic round progress for student UI."""
    job = app.job
    # Fetch rounds defined for this job
    hiring_rounds = HiringRound.query.filter_by(job_id=app.job_id).order_by(HiringRound.round_number).all()
    progress_map = {p.hiring_round_id: p for p in app.round_progresses}

    rounds = []
    cleared = 0
    for hr in hiring_rounds:
        pr = progress_map.get(hr.id)
        status = pr.status if pr else 'Pending'
        cleared += 1 if status in ('Passed', 'Completed') else 0
        rounds.append({
            'round_id': hr.id,
            'name': hr.round_name,
            'sequence': hr.round_number,
            'status': status,
            'is_elimination_round': hr.is_elimination_round,
            'scheduled_date': hr.scheduled_date.isoformat() if hr.scheduled_date else None,
            'scheduled_time': str(hr.scheduled_time) if hasattr(hr, 'scheduled_time') and hr.scheduled_time else None,
            'mode': hr.round_mode,
            'type': hr.round_type,
            'progress_id': pr.id if pr else None,
        })

    total_rounds = len(hiring_rounds)
    progress_pct = int((cleared / total_rounds) * 100) if total_rounds else 0

    return {
        'id': app.id,
        'student_id': app.student_id,
        'job_id': app.job_id,
        'job_title': job.title if job else None,
        'company_name': job.company.company_name if job and job.company else None,
        'status': app.status,
        'applied_at': app.applied_at.isoformat(),
        'updated_at': app.updated_at.isoformat(),
        'rounds': rounds,
        'rounds_total': total_rounds,
        'rounds_cleared': cleared,
        'progress_pct': progress_pct,
    }


# Register blueprints
from company_advanced_routes import company_bp
from admin_routes import admin_bp
from resume_routes import resume_bp, get_resume_text
from learning_guide_routes import learning_guide_bp
from hiring_rounds_routes import hiring_rounds_bp
from session_routes import session_bp
from email_reminder_routes import email_reminder_bp

app.register_blueprint(company_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(resume_bp)
app.register_blueprint(learning_guide_bp)
app.register_blueprint(hiring_rounds_bp)
app.register_blueprint(session_bp)
app.register_blueprint(email_reminder_bp)

# ==================== Authentication Routes ====================

@app.route('/api/batches/active', methods=['GET'])
def get_active_batches():
    """Get all active batches for registration (Public endpoint)"""
    try:
        batches = Batch.query.filter_by(status='Active').order_by(Batch.end_year.desc()).all()
        return jsonify([{
            'id': batch.id,
            'batch_code': batch.batch_code,
            'start_year': batch.start_year,
            'end_year': batch.end_year,
            'degree': batch.degree,
            'program': batch.program
        } for batch in batches]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/departments', methods=['GET'])
def get_departments():
    """Get all departments/branches (Public endpoint)"""
    try:
        departments = Department.query.all()
        return jsonify([{
            'id': dept.id,
            'name': dept.name,
            'full_name': dept.full_name
        } for dept in departments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user (Student, Company, or Admin)"""
    try:
        print(f'\n[REGISTER] ========== NEW REGISTRATION REQUEST ==========')
        print(f'[REGISTER] Request method: {request.method}')
        print(f'[REGISTER] Content-Type: {request.content_type}')
        
        data = request.get_json()
        print(f'[REGISTER] Received data keys: {list(data.keys()) if data else "None"}')
        print(f'[REGISTER] Email: {data.get("email", "N/A")}')
        print(f'[REGISTER] Role ID: {data.get("role_id", "N/A")}')
        
        # Check if user exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            print(f'[REGISTER] ERROR: Email {data["email"]} already registered')
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create user
        user = User(
            email=data['email'],
            role_id=data['role_id'],  # 1=Student, 2=Company, 3=Admin
            is_verified=False
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.flush()
        print(f'[REGISTER] User created with ID: {user.id}, Role: {user.role_id}')
        
        # Create role-specific profile
        if data['role_id'] == 1:  # Student
            print(f'[REGISTER] Creating Student profile...')
            student = Student(
                user_id=user.id,
                full_name=data['full_name'],
                enrollment_number=data['enrollment_number'],
                branch=data['branch'],
                cgpa=data['cgpa'],
                graduation_year=data['graduation_year'],
                current_year=data.get('current_year'),
                batch_id=data.get('batch_id'),
                phone=data.get('phone', '')
            )
            db.session.add(student)
            db.session.flush()  # Get student ID
            print(f'[REGISTER] Student created with ID: {student.id}')
            
            # DON'T create StudentVerification yet - only after OTP verification
            # Create temporary verification record to store OTP
            verification = StudentVerification(
                student_id=student.id,
                status='Pending',
                otp_verified=False
            )
            db.session.add(verification)
            print(f'[REGISTER] Temporary verification record created for OTP: {student.id}')
        
        elif data['role_id'] == 2:  # Company
            print(f'[REGISTER] Creating Company profile...')
            company = Company(
                user_id=user.id,
                company_name=data['company_name'],
                industry=data.get('industry', ''),
                hr_name=data['hr_name'],
                hr_phone=data.get('hr_phone', '')
            )
            db.session.add(company)
            print(f'[REGISTER] Company created')
        
        elif data['role_id'] == 3:  # Admin
            print(f'[REGISTER] Creating Admin profile...')
            # Verify admin creation key (optional - can be set via environment variable)
            admin_key = os.getenv('ADMIN_CREATION_KEY', '')
            if admin_key and data.get('verification_key') != admin_key:
                print(f'[REGISTER] ERROR: Invalid admin verification key')
                return jsonify({'error': 'Invalid admin verification key'}), 403
            
            admin = Admin(
                user_id=user.id,
                full_name=data['full_name'],
                email=data['email'],
                phone=data.get('phone', ''),
                department=data.get('department', 'Coordinator')
            )
            db.session.add(admin)
            db.session.flush()
            print(f'[REGISTER] Admin created with ID: {admin.id}')
            
            # Create admin verification request (not visible to admin until OTP verified)
            admin_verification = AdminVerification(
                admin_id=admin.id,
                status='Pending',
                otp_verified=False
            )
            db.session.add(admin_verification)
            print(f'[REGISTER] Temporary admin verification created for OTP: {admin.id}')
            
            # Create initial access log
            access_log = AdminAccessLog(
                admin_id=admin.id,
                action='created',
                status='Pending',
                details=f'Admin account created for {data.get("department", "Coordinator")} department'
            )
            db.session.add(access_log)
            print(f'[REGISTER] AdminAccessLog created')
        
        db.session.commit()
        print(f'[REGISTER] SUCCESS: User {data["email"]} registered successfully')
        
        # Send OTP email for verification
        print(f'[REGISTER] Generating and sending OTP...')
        role_type = 'student' if data['role_id'] == 1 else 'admin' if data['role_id'] == 3 else 'company'
        full_name = data.get('full_name') or data.get('company_name', 'User')
        
        # Get the verification record (Student or Admin)
        verification_record = None
        if data['role_id'] == 1:  # Student
            verification_record = StudentVerification.query.filter_by(student_id=user.student.id).first()
        elif data['role_id'] == 3:  # Admin
            verification_record = AdminVerification.query.filter_by(admin_id=user.admin_profile.id).first()
        
        # Generate and store OTP
        email_sent = None
        if verification_record:
            otp = generate_otp()
            verification_record.otp = otp
            verification_record.otp_sent_at = datetime.utcnow()
            verification_record.otp_verified = False
            verification_record.otp_attempts = 0
            db.session.commit()
            print(f'[REGISTER] OTP generated and stored: {otp}')
            
            # Send OTP email
            email_sent = send_otp_email(data['email'], full_name, otp)
            print(f'[REGISTER] OTP email sent to {data["email"]}: {email_sent}')
        
        return jsonify({
            'message': f'Registration successful! OTP sent to {data["email"]}. Please verify your email.' if email_sent else 'Registration successful, but OTP email could not be sent. Please use Resend OTP.',
            'user': user.to_dict(),
            'role_type': role_type,
            'email': data['email'],
            'next_step': 'otp_verification',
            'otp_email_sent': bool(email_sent)
        }), 201
        
    except Exception as e:
        print(f'\n[REGISTER] EXCEPTION OCCURRED')
        print(f'[REGISTER] Exception type: {type(e).__name__}')
        print(f'[REGISTER] Exception message: {str(e)}')
        import traceback
        print(f'[REGISTER] Traceback:\n{traceback.format_exc()}')
        
        try:
            db.session.rollback()
        except:
            pass
        
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to user email for verification"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        print(f'\n[OTP] ========== SEND OTP REQUEST ==========')
        print(f'[OTP] Email: {email}')
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f'[OTP] User not found: {email}')
            return jsonify({'error': 'Email not registered'}), 404
        
        # Get verification record
        verification_record = None
        full_name = 'User'
        role_type = None
        
        if user.role_id == 1:  # Student
            student = user.student
            if not student:
                return jsonify({'error': 'Student profile not found'}), 404
            verification_record = StudentVerification.query.filter_by(student_id=student.id).first()
            full_name = student.full_name
            role_type = 'student'
        elif user.role_id == 3:  # Admin
            admin = user.admin_profile
            if not admin:
                return jsonify({'error': 'Admin profile not found'}), 404
            verification_record = AdminVerification.query.filter_by(admin_id=admin.id).first()
            full_name = admin.full_name
            role_type = 'admin'
        else:
            return jsonify({'error': 'Invalid user role for OTP verification'}), 400
        
        if not verification_record:
            print(f'[OTP] Verification record not found for user: {email}')
            return jsonify({'error': 'Verification record not found'}), 404
        
        # Generate new OTP
        otp = generate_otp()
        verification_record.otp = otp
        verification_record.otp_sent_at = datetime.utcnow()
        verification_record.otp_verified = False
        verification_record.otp_attempts = 0
        db.session.commit()
        
        print(f'[OTP] OTP generated: {otp}')
        
        # Send OTP email
        email_sent = send_otp_email(email, full_name, otp)
        
        if not email_sent:
            print(f'[OTP] Failed to send OTP email')
            return jsonify({
                'success': False,
                'error': 'Failed to send OTP email. Please try again.',
                'message': 'Could not send verification code. Check your email settings.'
            }), 500
        
        print(f'[OTP] OTP sent successfully to {email}')
        
        return jsonify({
            'success': True,
            'message': f'OTP sent to {email}',
            'email': email,
            'otp_length': 6
        }), 200
        
    except Exception as e:
        print(f'[OTP] EXCEPTION in send_otp: {str(e)}')
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP submitted by user"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        
        if not email or not otp:
            return jsonify({'error': 'Email and OTP are required'}), 400
        
        print(f'\n[OTP] ========== VERIFY OTP REQUEST ==========')
        print(f'[OTP] Email: {email}')
        print(f'[OTP] OTP submitted: {otp}')
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f'[OTP] User not found: {email}')
            return jsonify({'error': 'Email not registered'}), 404
        
        # Get verification record
        verification_record = None
        full_name = 'User'
        role_type = None
        
        if user.role_id == 1:  # Student
            student = user.student
            if not student:
                return jsonify({'error': 'Student profile not found'}), 404
            verification_record = StudentVerification.query.filter_by(student_id=student.id).first()
            full_name = student.full_name
            role_type = 'student'
        elif user.role_id == 3:  # Admin
            admin = user.admin_profile
            if not admin:
                return jsonify({'error': 'Admin profile not found'}), 404
            verification_record = AdminVerification.query.filter_by(admin_id=admin.id).first()
            full_name = admin.full_name
            role_type = 'admin'
        else:
            return jsonify({'error': 'Invalid user role for OTP verification'}), 400
        
        if not verification_record:
            print(f'[OTP] Verification record not found for user: {email}')
            return jsonify({'error': 'Verification record not found'}), 404
        
        # Check OTP validity
        if not is_otp_valid(verification_record):
            print(f'[OTP] OTP expired for {email}')
            return jsonify({
                'error': 'OTP has expired',
                'message': 'Your verification code has expired. Please request a new one.',
                'expired': True
            }), 400
        
        # Check OTP attempts
        if verification_record.otp_attempts >= 5:
            print(f'[OTP] Too many failed attempts for {email}')
            return jsonify({
                'error': 'Too many failed attempts. Please request a new OTP.',
                'too_many_attempts': True
            }), 429
        
        # Verify OTP
        if verification_record.otp != otp:
            verification_record.otp_attempts += 1
            db.session.commit()
            attempts_left = 5 - verification_record.otp_attempts
            
            print(f'[OTP] OTP mismatch for {email}. Attempts left: {attempts_left}')
            
            return jsonify({
                'error': 'Invalid OTP',
                'message': f'Incorrect verification code. {attempts_left} attempts remaining.',
                'attempts_remaining': attempts_left
            }), 401
        
        # OTP verified successfully
        verification_record.otp_verified = True
        verification_record.otp_verified_at = datetime.utcnow()
        verification_record.otp_attempts = 0
        db.session.commit()
        
        print(f'[OTP] OTP verified successfully for {email}')
        
        # Send approval pending email
        send_approval_pending_email(email, full_name, role_type)
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully!',
            'email_verified': True,
            'user': user.to_dict(),
            'next_step': 'await_admin_approval'
        }), 200
        
    except Exception as e:
        print(f'[OTP] EXCEPTION in verify_otp: {str(e)}')
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Require OTP verification for student/admin accounts (skip for demo accounts)
        demo_emails = ['admin@university.edu', 'student@university.edu', 'company@tech.com']
        if user.role_id in (1, 3) and user.email not in demo_emails:
            verification_record = None
            if user.role_id == 1 and user.student:
                verification_record = StudentVerification.query.filter_by(student_id=user.student.id).first()
            elif user.role_id == 3 and user.admin_profile:
                verification_record = AdminVerification.query.filter_by(admin_id=user.admin_profile.id).first()
            if not verification_record or not verification_record.otp_verified:
                return jsonify({'error': 'Email not verified. Please complete OTP verification.'}), 403

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
        student.tenth_percentage = data.get('tenth_percentage', student.tenth_percentage)
        student.twelfth_percentage = data.get('twelfth_percentage', student.twelfth_percentage)
        student.experience = data.get('experience', student.experience)
        student.projects = data.get('projects', student.projects)
        student.certifications = data.get('certifications', student.certifications)
        student.linkedin_url = data.get('linkedin_url', student.linkedin_url)
        student.github_url = data.get('github_url', student.github_url)
        
        # Check profile completion
        if all([student.full_name, student.phone, student.cgpa, student.skills]):
            student.profile_completed = True
        
        db.session.commit()

        if data.get('skills'):
            _sync_skill_master_from_student(data.get('skills'))
        return jsonify(student.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/jobs', methods=['GET'])
@jwt_required()
def get_student_jobs():
    """Get all jobs with eligibility status for the student - SESSION AWARE"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        if not student:
            return jsonify({'error': 'Student profile not found'}), 404
            
        student_branch = student.branch.lower() if student.branch else ''
        student_cgpa = student.cgpa or 0
        
        # Get active placement session
        from models import PlacementSession, BatchSessionMapping
        active_session = PlacementSession.query.filter_by(status='Active').first()
        
        if not active_session:
            # Fallback to default session
            active_session = PlacementSession.query.filter_by(is_default=True).first()
        
        # Build query with session filter
        query = Job.query.filter(Job.status == 'Approved')
        
        if active_session:
            query = query.filter(Job.session_id == active_session.id)
            
            # Also filter by batch eligibility
            if student.batch_id:
                # Check if student's batch is eligible for this session
                batch_eligible = BatchSessionMapping.query.filter_by(
                    batch_id=student.batch_id,
                    session_id=active_session.id,
                    is_eligible=True
                ).first()
                
                if not batch_eligible:
                    # Student's batch not eligible for active session
                    return jsonify([]), 200
        
        jobs = query.order_by(Job.application_deadline.asc()).all()
        
        # Check which jobs student has already applied to
        applied_job_ids = [app.job_id for app in student.applications]
        
        jobs_data = []
        for job in jobs:
            job_dict = job.to_dict()
            job_dict['has_applied'] = job.id in applied_job_ids
            
            # Check eligibility
            is_eligible = True
            eligibility_reasons = []
            
            # Check CGPA requirement
            if job.min_cgpa and student_cgpa < job.min_cgpa:
                is_eligible = False
                eligibility_reasons.append(f"Min CGPA required: {job.min_cgpa} (Your CGPA: {student_cgpa})")
            
            # Check branch requirement
            if job.eligible_branches:
                # If branches is set to "All", skip branch check
                if job.eligible_branches.strip().lower() != 'all':
                    branches_list = [b.strip().lower() for b in job.eligible_branches.split(',')]
                    student_branch_lower = student_branch.lower()
                    
                    # Flexible branch matching:
                    # 1. Exact match
                    # 2. Student branch contains any eligible branch
                    # 3. Any eligible branch contains student branch
                    # 4. Common abbreviations (IT = Information Technology, CS = Computer Science, ECE = Electronics)
                    branch_aliases = {
                        'it': ['information technology', 'it', 'i.t.', 'i.t'],
                        'cs': ['computer science', 'cs', 'c.s.', 'cse', 'computer science and engineering'],
                        'ece': ['electronics', 'electronics and communication', 'ece', 'e.c.e.'],
                        'ee': ['electrical', 'electrical engineering', 'ee', 'e.e.'],
                        'me': ['mechanical', 'mechanical engineering', 'me', 'm.e.'],
                        'ce': ['civil', 'civil engineering', 'ce', 'c.e.'],
                    }
                    
                    branch_match = False
                    
                    # Direct check
                    for eligible_branch in branches_list:
                        if student_branch_lower == eligible_branch:
                            branch_match = True
                            break
                        if student_branch_lower in eligible_branch or eligible_branch in student_branch_lower:
                            branch_match = True
                            break
                    
                    # Alias check if no direct match
                    if not branch_match:
                        for alias_key, aliases in branch_aliases.items():
                            # If student branch matches any alias
                            student_in_alias = student_branch_lower in aliases or any(a in student_branch_lower for a in aliases)
                            if student_in_alias:
                                # Check if any eligible branch matches the same alias group
                                for eligible_branch in branches_list:
                                    if eligible_branch in aliases or any(a in eligible_branch for a in aliases):
                                        branch_match = True
                                        break
                            if branch_match:
                                break
                    
                    if not branch_match:
                        is_eligible = False
                        eligibility_reasons.append(f"Branch not eligible. Required: {job.eligible_branches}")
            
            job_dict['is_eligible'] = is_eligible
            job_dict['eligibility_reasons'] = eligibility_reasons
            jobs_data.append(job_dict)
        
        return jsonify(jobs_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/apply/<int:job_id>', methods=['POST'])
@jwt_required()
def apply_to_job(job_id):
    """Apply to a job - SESSION AWARE"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        # Check if profile is completed
        if not student.profile_completed:
            return jsonify({'error': 'Please complete your profile before applying'}), 400
        
        # Get the job
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # SESSION VALIDATION: Check if student's batch is eligible for this job's session
        if job.session_id and student.batch_id:
            from models import BatchSessionMapping
            batch_eligible = BatchSessionMapping.query.filter_by(
                batch_id=student.batch_id,
                session_id=job.session_id,
                is_eligible=True
            ).first()
            
            if not batch_eligible:
                return jsonify({'error': 'Your batch is not eligible for this placement session'}), 403
        
        # Check if already applied
        existing = Application.query.filter_by(
            student_id=student.id,
            job_id=job_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Already applied to this job'}), 400
        
        # Create application with session context
        application = Application(
            student_id=student.id,
            job_id=job_id,
            session_id=job.session_id,
            status='Applied'
        )
        db.session.add(application)
        db.session.flush()

        # Seed per-round progress for this job (if rounds defined)
        hiring_rounds = HiringRound.query.filter_by(job_id=job_id).order_by(HiringRound.round_number).all()
        app_rounds = []
        for hr in hiring_rounds:
            app_rounds.append(ApplicationRound(
                application_id=application.id,
                hiring_round_id=hr.id,
                status='Pending'
            ))
        if app_rounds:
            db.session.add_all(app_rounds)

        db.session.commit()
        
        return jsonify({
            'message': 'Application submitted successfully',
            'application': serialize_application(application)
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
        
        student = user.student
        if not student:
            return jsonify({'error': 'Student profile not found'}), 404
            
        applications = student.applications
        # Serialize with dynamic round progress
        payload = [serialize_application(app) for app in applications]
        return jsonify(payload), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/company-visits', methods=['GET'])
@jwt_required()
def get_company_visits():
    """Get upcoming company visits/drives"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Try to get from database, return empty list if table doesn't exist
        try:
            from models import CompanyVisit
            visits = CompanyVisit.query.filter(
                CompanyVisit.status.in_(['Scheduled', 'Ongoing'])
            ).order_by(CompanyVisit.visit_date.asc()).all()
            return jsonify([v.to_dict() for v in visits]), 200
        except:
            return jsonify([]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/notifications', methods=['GET'])
@jwt_required()
def get_student_notifications():
    """Get student's notifications"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Try to get from database, return empty list if table doesn't exist
        try:
            from models import Notification
            notifications = Notification.query.filter_by(
                student_id=user.student.id
            ).order_by(Notification.created_at.desc()).limit(20).all()
            return jsonify([n.to_dict() for n in notifications]), 200
        except:
            return jsonify([]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/interview-experiences', methods=['GET'])
@jwt_required()
def get_interview_experiences():
    """Get community shared interview experiences"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Try to get from database, return empty list if table doesn't exist
        try:
            from models import InterviewExperience
            experiences = InterviewExperience.query.filter_by(
                is_public=True
            ).order_by(InterviewExperience.created_at.desc()).limit(20).all()
            return jsonify([e.to_dict() for e in experiences]), 200
        except:
            return jsonify([]), 200
        
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
            # GET: Filter jobs by session if provided
            session_id = request.args.get('session_id', type=int)
            
            if session_id:
                jobs = Job.query.filter_by(company_id=company.id, session_id=session_id).all()
            else:
                jobs = company.jobs
            
            return jsonify([job.to_dict() for job in jobs]), 200
        
        # POST - Create new job (SESSION REQUIRED)
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No job data provided'}), 400

        required_fields = ['title', 'job_type', 'description', 'application_deadline', 'session_id']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400

        # Validate session exists and is active/upcoming
        from models import PlacementSession
        session_id = data.get('session_id')
        session = PlacementSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Invalid session_id'}), 400
        
        if session.status not in ['Active', 'Upcoming']:
            return jsonify({'error': 'Can only post jobs to Active or Upcoming sessions'}), 400

        # Parse and validate deadline
        deadline_str = data.get('application_deadline')
        deadline_date = None
        if deadline_str:
            try:
                deadline_date = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except Exception:
                return jsonify({'error': 'Invalid application_deadline format. Use YYYY-MM-DD'}), 400
        if not deadline_date:
            return jsonify({'error': 'application_deadline is required'}), 400

        job = Job(
            company_id=company.id,
            title=data.get('title'),
            job_type=data.get('job_type'),
            description=data.get('description', ''),
            requirements=data.get('requirements', ''),
            location=data.get('location', ''),
            salary_range=data.get('salary_range', ''),
            min_cgpa=float(data.get('min_cgpa', 0.0) or 0.0),
            eligible_branches=data.get('eligible_branches', ''),
            application_deadline=deadline_date,
            session_id=session_id,
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


@app.route('/api/company/jobs/<int:job_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def update_or_delete_job(job_id):
    """Update or delete a specific job posting"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 2:
            return jsonify({'error': 'Unauthorized'}), 403
        
        company = user.company
        if not company:
            return jsonify({'error': 'Company profile not found'}), 404
        
        # Verify job belongs to this company
        job = Job.query.filter_by(id=job_id, company_id=company.id).first()
        if not job:
            return jsonify({'error': 'Job not found or access denied'}), 404
        
        if request.method == 'PUT':
            # Update job
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Update fields if provided
            if 'title' in data:
                job.title = data['title']
            if 'job_type' in data:
                job.job_type = data['job_type']
            if 'description' in data:
                job.description = data['description']
            if 'requirements' in data:
                job.requirements = data['requirements']
            if 'location' in data:
                job.location = data['location']
            if 'salary_range' in data:
                job.salary_range = data['salary_range']
            if 'min_cgpa' in data:
                job.min_cgpa = float(data['min_cgpa'] or 0.0)
            if 'eligible_branches' in data:
                job.eligible_branches = data['eligible_branches']
            if 'application_deadline' in data:
                try:
                    job.application_deadline = datetime.strptime(data['application_deadline'], '%Y-%m-%d').date()
                except:
                    return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
            # Reset to pending if job was previously approved (requires re-approval after edit)
            if job.status == 'Approved':
                job.status = 'Pending'
            
            db.session.commit()
            
            return jsonify({
                'message': 'Job updated successfully. Awaiting admin re-approval.',
                'job': job.to_dict()
            }), 200
        
        elif request.method == 'DELETE':
            # Delete job and all related data
            db.session.delete(job)
            db.session.commit()
            
            return jsonify({
                'message': 'Job deleted successfully'
            }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/company/job/<int:job_id>/applicants', methods=['GET'])
@jwt_required()
def get_job_applicants(job_id):
    """Get all applicants for a specific job with ATS scores"""
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
            # Add ATS score fields
            student_data['ats_score'] = app.student.ats_score
            student_data['ats_feedback'] = app.student.ats_feedback
            student_data['ats_calculated_at'] = app.student.ats_calculated_at.isoformat() if app.student.ats_calculated_at else None
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
        
        # Send email notification based on status change
        try:
            from email_service import send_application_status_update, send_shortlist_notification, send_offer_letter
            
            student = application.student
            job = application.job
            
            if student.user and student.user.email:
                status = data['status']
                
                if status == 'Shortlisted':
                    send_shortlist_notification(
                        user_email=student.user.email,
                        full_name=student.full_name,
                        job_title=job.title,
                        company_name=job.company.company_name
                    )
                elif status == 'Offered':
                    # Check if offer letter exists for more details
                    offer = OfferLetter.query.filter_by(
                        student_id=student.id,
                        job_id=job.id
                    ).first()
                    
                    if offer:
                        send_offer_letter(
                            user_email=student.user.email,
                            full_name=student.full_name,
                            job_title=job.title,
                            company_name=job.company.company_name,
                            package=f"{offer.annual_ctc} LPA",
                            joining_date=offer.joining_date.strftime('%B %d, %Y') if offer.joining_date else None
                        )
                    else:
                        send_application_status_update(
                            user_email=student.user.email,
                            full_name=student.full_name,
                            job_title=job.title,
                            company_name=job.company.company_name,
                            new_status=status
                        )
                else:
                    # Send general status update for other statuses
                    send_application_status_update(
                        user_email=student.user.email,
                        full_name=student.full_name,
                        job_title=job.title,
                        company_name=job.company.company_name,
                        new_status=status,
                        message=data.get('notes')
                    )
                
                print(f"✉️ Status update email sent to {student.full_name}")
        except Exception as email_error:
            print(f"⚠️ Email notification failed (but status updated): {str(email_error)}")
        
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
            if not student:
                continue  # Skip applications without student profiles
            ws.append([
                student.full_name,
                student.enrollment_number,
                student.branch or 'N/A',
                float(student.cgpa) if student.cgpa else 0.0,
                student.phone or 'N/A',
                student.user.email if student.user else 'N/A',
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
        
        # Placement statistics - using OfferLetter for consistency
        placed_students = db.session.query(func.count(func.distinct(OfferLetter.student_id))).filter(
            OfferLetter.status.in_(['Sent', 'Accepted'])
        ).scalar() or 0
        
        # Branch-wise statistics - ALL branches with placement data
        branch_data = []
        branches = db.session.query(Student.branch).distinct().all()
        for (branch,) in branches:
            total = Student.query.filter_by(branch=branch).count()
            # Count students with offer letters
            placed = db.session.query(func.count(func.distinct(OfferLetter.student_id))).join(
                Student, OfferLetter.student_id == Student.id
            ).filter(
                Student.branch == branch,
                OfferLetter.status.in_(['Sent', 'Accepted'])
            ).scalar() or 0
            
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


# ==================== ATS Scoring Integration ====================

@app.route('/api/student/ats-score/<int:job_id>', methods=['GET'])
@jwt_required()
def get_ats_score_for_job(job_id):
    """Calculate ATS score for a specific job"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        # Check if student has resume
        if not student.resume_url:
            return jsonify({'error': 'No resume uploaded. Please upload your resume first.'}), 400
        
        # Get job details
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Extract resume text (Drive/local aware)
        from ats_scorer import calculate_ats_score
        resume_text, error = get_resume_text(student)
        if error:
            status = 404 if 'not found' in error.lower() else 400
            return jsonify({'error': error}), status
        
        # Build JD text from job details
        jd_text = f"""
{job.title}

Company: {job.company.company_name if job.company else 'N/A'}
Location: {job.location or 'N/A'}

Job Description:
{job.description}

Required Skills:
{job.requirements or 'Not specified'}

Minimum CGPA: {job.min_cgpa}
Eligible Branches: {job.eligible_branches or 'All'}
Experience Required: Check description
        """.strip()
        
        # Calculate ATS score
        result = calculate_ats_score(resume_text, jd_text)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'job_title': job.title,
            'company_name': job.company.company_name if job.company else 'N/A',
            'ats_score': round(result['score']),
            'level': result['level'],
            'summary': result['summary']
        }), 200
        
    except Exception as e:
        import traceback
        print(f"ATS Score Error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/ats-analysis/<int:job_id>', methods=['GET'])
@jwt_required()
def get_ats_analysis_for_job(job_id):
    """Get detailed ATS analysis with heatmap data for a specific job"""
    try:
        user_id = get_user_id()
        user = User.query.get(user_id)
        
        if user.role_id != 1:
            return jsonify({'error': 'Unauthorized'}), 403
        
        student = user.student
        
        # Check if student has resume
        if not student.resume_url:
            return jsonify({'error': 'No resume uploaded. Please upload your resume first.'}), 400
        
        # Get job details
        job = Job.query.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Extract resume text (Drive/local aware)
        from ats_scorer import calculate_ats_score
        resume_text, error = get_resume_text(student)
        if error:
            status = 404 if 'not found' in error.lower() else 400
            return jsonify({'error': error}), status
        
        # Build JD text from job details
        jd_text = f"""
{job.title}

Company: {job.company.company_name if job.company else 'N/A'}
Location: {job.location or 'N/A'}

Job Description:
{job.description}

Required Skills:
{job.requirements or 'Not specified'}

Minimum CGPA: {job.min_cgpa}
Eligible Branches: {job.eligible_branches or 'All'}
Experience Required: Check description
        """.strip()
        
        # Calculate ATS score with full details
        result = calculate_ats_score(resume_text, jd_text)
        report = result['report']
        
        # Build recommendations
        recommendations = []
        score = result['score']
        
        if score >= 85:
            recommendations = [
                "Apply immediately - you're a strong candidate",
                "Tailor your cover letter to highlight matching skills",
                "Prepare to discuss your relevant projects in detail"
            ]
        elif score >= 70:
            recommendations = [
                "Apply with confidence",
                "Address any missing skills in your cover letter",
                "Highlight your transferable experience"
            ]
        elif score >= 55:
            recommendations = [
                "Consider applying if you're a fast learner",
                "Take online courses for missing critical skills",
                "Build projects showcasing required technologies"
            ]
        else:
            recommendations = [
                "Focus on building required skills first",
                "Look for junior/entry-level positions",
                "Create portfolio projects using required technologies"
            ]
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'job_title': job.title,
            'company_name': job.company.company_name if job.company else 'N/A',
            'ats_score': round(result['score']),
            'level': result['level'],
            'summary': result['summary'],
            'scores': report['scores'],
            'strengths': report['strengths'],
            'missing_required': report['missing_required'],
            'preferred_matched': report['preferred_matched'],
            'preferred_missing': report['preferred_missing'],
            'resume_details': report['resume_details'],
            'jd_details': report['jd_details'],
            'heatmap_data': result['heatmap_data'],
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        import traceback
        print(f"ATS Analysis Error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500


# ==================== Health Check ====================

@app.route('/', methods=['GET'])
def root():
    """Root endpoint for browsers/uptime checks."""
    return jsonify({
        'status': 'ok',
        'message': 'Placement Portal API is running',
        'health': '/api/health',
    }), 200


@app.route('/api', methods=['GET'])
def api_root():
    """API root endpoint to avoid confusing 404s when visiting /api."""
    return jsonify({
        'status': 'ok',
        'message': 'Placement Portal API',
        'health': '/api/health',
    }), 200


@app.route('/favicon.ico', methods=['GET'])
def favicon():
    """Avoid noisy 404s in browser consoles."""
    return ('', 204)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Placement Portal API is running'}), 200


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all uncaught exceptions"""
    # Preserve HTTP errors (e.g., 404/405) with their correct status codes.
    # Without this, Werkzeug HTTPExceptions can be converted into 500s.
    if isinstance(error, HTTPException):
        return jsonify({'error': error.description}), error.code

    db.session.rollback()
    return jsonify({'error': str(error)}), 500


if __name__ == '__main__':
    debug_env = os.getenv('FLASK_DEBUG', '0').strip().lower()
    debug = debug_env in ('1', 'true', 'yes', 'y', 'on')
    # Avoid the reloader in this environment; it can cause the process to exit
    # and leads to frontend "Failed to fetch" when nothing is listening.
    app.run(debug=debug, host='0.0.0.0', port=5000, use_reloader=False)

