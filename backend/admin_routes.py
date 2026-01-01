"""
Admin (TPO) Dashboard Routes
Comprehensive management and analytics endpoints for admin users
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, StudentVerification, StudentBlacklist, Department, BatchYear, Skill, PlacementStats, CompanyVisit, Student, User, Application, OfferLetter, Job
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import json

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def get_user_id():
    """Convert JWT identity (string) to integer user_id"""
    identity = get_jwt_identity()
    return int(identity) if identity else None

def check_admin(user_id):
    """Verify user is admin"""
    user = User.query.get(user_id)
    return user and user.role_id == 3

# ==================== STUDENT VERIFICATION ENDPOINTS ====================

@admin_bp.route('/verification-queue', methods=['GET'])
@jwt_required()
def get_verification_queue():
    """Get paginated list of students pending document verification"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', 'Pending')
        
        query = StudentVerification.query
        
        if status_filter != 'All':
            query = query.filter_by(status=status_filter)
        
        # Server-side pagination
        total = query.count()
        verifications = query.order_by(StudentVerification.submitted_at.desc()).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'data': [v.to_dict() for v in verifications.items],
            'pagination': {
                'total': total,
                'pages': verifications.pages,
                'current_page': page,
                'per_page': per_page
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/verification/<int:verification_id>/approve', methods=['POST'])
@jwt_required()
def approve_student_verification(verification_id):
    """Approve student document verification and activate account"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        verification = StudentVerification.query.get(verification_id)
        if not verification:
            return jsonify({'error': 'Verification record not found'}), 404
        
        # Update verification status
        verification.status = 'Verified'
        verification.verification_date = datetime.utcnow()
        verification.verified_by = user_id
        
        # Activate student's user account
        user = User.query.get(verification.student.user_id)
        if user:
            user.is_verified = True
            user.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f"Student {verification.student.full_name} verified successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/verification/<int:verification_id>/reject', methods=['POST'])
@jwt_required()
def reject_student_verification(verification_id):
    """Reject student documents with reason"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        rejection_reason = data.get('rejection_reason', '')
        
        verification = StudentVerification.query.get(verification_id)
        if not verification:
            return jsonify({'error': 'Verification record not found'}), 404
        
        verification.status = 'Rejected'
        verification.rejection_reason = rejection_reason
        verification.verification_date = datetime.utcnow()
        verification.verified_by = user_id
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f"Student {verification.student.full_name} rejected"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== BLACKLIST MANAGEMENT ENDPOINTS ====================

@admin_bp.route('/blacklist/students', methods=['GET'])
@jwt_required()
def get_blacklisted_students():
    """Get list of blacklisted students"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        blacklisted = StudentBlacklist.query.filter_by(is_blacklisted=True).all()
        
        return jsonify({
            'success': True,
            'data': [b.to_dict() for b in blacklisted]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/blacklist/add', methods=['POST'])
@jwt_required()
def blacklist_student():
    """Blacklist a student (freeze account)"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        student_id = data.get('student_id')
        reason = data.get('reason', '')
        severity = data.get('severity', 'Medium')
        duration_days = data.get('duration_days', None)  # If temporary
        
        # Check if already blacklisted
        existing = StudentBlacklist.query.filter_by(student_id=student_id).first()
        if existing:
            return jsonify({'error': 'Student already blacklisted'}), 400
        
        unblacklist_date = None
        if duration_days:
            unblacklist_date = datetime.utcnow() + timedelta(days=duration_days)
        
        blacklist = StudentBlacklist(
            student_id=student_id,
            is_blacklisted=True,
            reason=reason,
            severity=severity,
            blacklisted_by=user_id,
            unblacklist_date=unblacklist_date
        )
        
        db.session.add(blacklist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f"Student blacklisted successfully",
            'data': blacklist.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/blacklist/remove/<int:blacklist_id>', methods=['POST'])
@jwt_required()
def remove_student_blacklist(blacklist_id):
    """Remove student from blacklist"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        blacklist = StudentBlacklist.query.get(blacklist_id)
        if not blacklist:
            return jsonify({'error': 'Blacklist record not found'}), 404
        
        blacklist.is_blacklisted = False
        blacklist.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Student removed from blacklist'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== MASTER DATA MANAGEMENT ====================

# DEPARTMENTS
@admin_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_departments():
    """Get all departments"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        departments = Department.query.all()
        return jsonify({
            'success': True,
            'data': [d.to_dict() for d in departments]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments', methods=['POST'])
@jwt_required()
def add_department():
    """Add new department"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Check if exists
        if Department.query.filter_by(code=data.get('code')).first():
            return jsonify({'error': 'Department code already exists'}), 400
        
        dept = Department(
            name=data.get('name'),
            code=data.get('code'),
            description=data.get('description', ''),
            is_active=True
        )
        
        db.session.add(dept)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': dept.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@jwt_required()
def update_department(dept_id):
    """Update department"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        dept = Department.query.get(dept_id)
        if not dept:
            return jsonify({'error': 'Department not found'}), 404
        
        data = request.get_json()
        dept.name = data.get('name', dept.name)
        dept.description = data.get('description', dept.description)
        dept.is_active = data.get('is_active', dept.is_active)
        dept.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'data': dept.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# BATCH YEARS
@admin_bp.route('/batch-years', methods=['GET'])
@jwt_required()
def get_batch_years():
    """Get all batch years"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        years = BatchYear.query.all()
        return jsonify({
            'success': True,
            'data': [y.to_dict() for y in years]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/batch-years', methods=['POST'])
@jwt_required()
def add_batch_year():
    """Add new batch year"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if BatchYear.query.filter_by(year=data.get('year')).first():
            return jsonify({'error': 'Batch year already exists'}), 400
        
        year = BatchYear(
            year=data.get('year'),
            academic_session=data.get('academic_session'),
            is_active=True
        )
        
        db.session.add(year)
        db.session.commit()
        
        return jsonify({'success': True, 'data': year.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# SKILLS
@admin_bp.route('/skills', methods=['GET'])
@jwt_required()
def get_skills():
    """Get all skills"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        skills = Skill.query.all()
        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in skills]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/skills', methods=['POST'])
@jwt_required()
def add_skill():
    """Add new skill"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if Skill.query.filter_by(name=data.get('name')).first():
            return jsonify({'error': 'Skill already exists'}), 400
        
        skill = Skill(
            name=data.get('name'),
            category=data.get('category'),
            description=data.get('description', ''),
            is_active=True
        )
        
        db.session.add(skill)
        db.session.commit()
        
        return jsonify({'success': True, 'data': skill.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== ANALYTICS ENDPOINTS ====================

@admin_bp.route('/analytics/placement-stats', methods=['GET'])
@jwt_required()
def get_placement_stats():
    """Get current placement statistics"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get latest stats or calculate
        stats = PlacementStats.query.order_by(PlacementStats.date.desc()).first()
        
        if not stats:
            # Calculate from current data
            total_students = Student.query.count()
            
            # Count placed students (those with selected offers)
            placed_students = db.session.query(func.count(func.distinct(OfferLetter.student_id))).filter(
                OfferLetter.status.in_(['Sent', 'Accepted'])
            ).scalar() or 0
            
            unplaced = total_students - placed_students
            
            # Calculate package stats
            offers = OfferLetter.query.filter(OfferLetter.status.in_(['Sent', 'Accepted'])).all()
            packages = [float(o.annual_ctc) if o.annual_ctc else 0 for o in offers]
            
            highest_package = max(packages) if packages else 0
            average_package = sum(packages) / len(packages) if packages else 0
            
            # Department-wise stats
            dept_stats = {}
            departments = Department.query.all()
            for dept in departments:
                dept_total = Student.query.filter_by(branch=dept.name).count()
                dept_placed = db.session.query(func.count(func.distinct(OfferLetter.student_id))).join(
                    Student, OfferLetter.student_id == Student.id
                ).filter(
                    Student.branch == dept.name,
                    OfferLetter.status.in_(['Sent', 'Accepted'])
                ).scalar() or 0
                
                dept_stats[dept.name] = {
                    'total': dept_total,
                    'placed': dept_placed,
                    'placement_rate': (dept_placed / dept_total * 100) if dept_total > 0 else 0
                }
            
            stats = PlacementStats(
                date=datetime.utcnow().date(),
                total_students=total_students,
                placed_students=placed_students,
                unplaced_students=unplaced,
                highest_package=highest_package,
                average_package=average_package,
                department_stats=dept_stats,
                total_companies_visiting=Job.query.filter(Job.status == 'Approved').count()
            )
            db.session.add(stats)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'data': stats.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics/company-visits', methods=['GET'])
@jwt_required()
def get_company_visits():
    """Get current company visits and their status"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get active company visits
        visits = CompanyVisit.query.filter(
            CompanyVisit.status.in_(['Scheduled', 'Interview Stage', 'Offer Stage'])
        ).order_by(CompanyVisit.visit_date.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [v.to_dict() for v in visits]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics/conflict-check', methods=['GET'])
@jwt_required()
def check_scheduling_conflicts():
    """Check for conflicting company visits (same date/time)"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get all scheduled visits
        visits = CompanyVisit.query.filter(
            CompanyVisit.status.in_(['Scheduled', 'Interview Stage'])
        ).all()
        
        conflicts = []
        
        # Find conflicts (visits within same hour on same date)
        for i, v1 in enumerate(visits):
            for v2 in visits[i+1:]:
                date_match = v1.visit_date.date() == v2.visit_date.date()
                time_diff = abs((v1.visit_date - v2.visit_date).total_seconds() / 3600)
                
                if date_match and time_diff < 2:  # 2-hour window
                    conflicts.append({
                        'company1': v1.company.company_name,
                        'company2': v2.company.company_name,
                        'scheduled_date': v1.visit_date.isoformat(),
                        'severity': 'Critical' if time_diff < 1 else 'Warning'
                    })
        
        return jsonify({
            'success': True,
            'conflicts_found': len(conflicts) > 0,
            'conflicts': conflicts
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/analytics/department-stats', methods=['GET'])
@jwt_required()
def get_department_stats():
    """Get placement stats by department"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        departments = Department.query.all()
        stats = []
        
        for dept in departments:
            total = Student.query.filter_by(branch=dept.name).count()
            placed = db.session.query(func.count(func.distinct(OfferLetter.student_id))).join(
                Student, OfferLetter.student_id == Student.id
            ).filter(
                Student.branch == dept.name,
                OfferLetter.status.in_(['Sent', 'Accepted'])
            ).scalar() or 0
            
            stats.append({
                'department': dept.name,
                'total_students': total,
                'placed': placed,
                'unplaced': total - placed,
                'placement_rate': (placed / total * 100) if total > 0 else 0
            })
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== REPORTS & EXPORT ====================

@admin_bp.route('/reports/student-data', methods=['GET'])
@jwt_required()
def export_student_data():
    """Export student data (for Excel or PDF)"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        students = Student.query.all()
        
        data = []
        for student in students:
            user = User.query.get(student.user_id)
            placed = OfferLetter.query.filter_by(student_id=student.id).first() is not None
            
            data.append({
                'enrollment_number': student.enrollment_number,
                'full_name': student.full_name,
                'email': user.email if user else '',
                'branch': student.branch,
                'cgpa': float(student.cgpa),
                'graduation_year': student.graduation_year,
                'is_placed': 'Yes' if placed else 'No',
                'profile_completed': 'Yes' if student.profile_completed else 'No'
            })
        
        return jsonify({
            'success': True,
            'data': data,
            'total_records': len(data)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/reports/placement-report', methods=['GET'])
@jwt_required()
def get_placement_report():
    """Get comprehensive placement report"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Calculate all stats
        total_students = Student.query.count()
        placed_students = db.session.query(func.count(func.distinct(OfferLetter.student_id))).filter(
            OfferLetter.status.in_(['Sent', 'Accepted'])
        ).scalar() or 0
        
        offers = OfferLetter.query.filter(OfferLetter.status.in_(['Sent', 'Accepted'])).all()
        packages = [float(o.annual_ctc) if o.annual_ctc else 0 for o in offers]
        
        highest = max(packages) if packages else 0
        average = sum(packages) / len(packages) if packages else 0
        
        # Department breakdown
        dept_stats = []
        for dept in Department.query.all():
            total = Student.query.filter_by(branch=dept.name).count()
            placed = db.session.query(func.count(func.distinct(OfferLetter.student_id))).join(
                Student, OfferLetter.student_id == Student.id
            ).filter(
                Student.branch == dept.name,
                OfferLetter.status.in_(['Sent', 'Accepted'])
            ).scalar() or 0
            
            dept_stats.append({
                'department': dept.name,
                'total': total,
                'placed': placed,
                'rate': (placed / total * 100) if total > 0 else 0
            })
        
        return jsonify({
            'success': True,
            'report': {
                'timestamp': datetime.utcnow().isoformat(),
                'total_students': total_students,
                'placed_students': placed_students,
                'unplaced_students': total_students - placed_students,
                'placement_rate': (placed_students / total_students * 100) if total_students > 0 else 0,
                'highest_package': float(highest),
                'average_package': float(average),
                'total_companies': Job.query.filter(Job.status == 'Approved').count(),
                'department_breakdown': dept_stats
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
