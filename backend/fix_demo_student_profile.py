"""
Fix demo student account by ensuring it has a student profile
Run this with: python -m flask shell < fix_demo_student_profile.py
Or access via endpoint: /api/admin/fix-demo-accounts
"""

def fix_demo_accounts_in_app():
    """Add student/company profiles to demo accounts if missing"""
    from models import User, Student, Company, db
    
    # Fix student account
    student_user = User.query.filter_by(email='student@university.edu').first()
    if student_user and not student_user.student:
        print('Creating student profile for student@university.edu...')
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
        print('✓ Student profile created')
    elif student_user and student_user.student:
        print('✓ Student profile already exists')
    else:
        print('⚠ No student user found')
    
    # Fix company account
    company_user = User.query.filter_by(email='company@tech.com').first()
    if company_user and not company_user.company:
        print('Creating company profile for company@tech.com...')
        company = Company(
            user_id=company_user.id,
            company_name='Demo Tech Corp',
            industry='Technology',
            hr_name='Demo HR',
            hr_phone='8888888888'
        )
        db.session.add(company)
        print('✓ Company profile created')
    elif company_user and company_user.company:
        print('✓ Company profile already exists')
    else:
        print('⚠ No company user found')
    
    db.session.commit()
    print('\n✅ All demo accounts fixed!')
    return True
