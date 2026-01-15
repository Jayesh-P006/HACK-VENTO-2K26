import os
import pymysql
from werkzeug.security import generate_password_hash
from urllib.parse import urlparse

# Get Railway MySQL URL
mysql_url = os.getenv('MYSQL_PUBLIC_URL') or os.getenv('DATABASE_URL')
if not mysql_url:
    print("Error: MYSQL_PUBLIC_URL not found")
    exit(1)

# Parse URL
parsed = urlparse(mysql_url)
host = parsed.hostname
port = parsed.port or 3306
user = parsed.username
password = parsed.password
database = parsed.path.lstrip('/')

print(f"Connecting to {host}:{port}/{database}...")

# Database connection
conn = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    database=database,
    autocommit=True
)

cursor = conn.cursor()

# Generate password hashes
admin_hash = generate_password_hash('admin123')
student_hash = generate_password_hash('student123')
company_hash = generate_password_hash('company123')

print("Creating demo accounts...")

# Check if demo accounts already exist
cursor.execute("SELECT id, email, role_id FROM users WHERE email IN ('admin@university.edu', 'student@university.edu', 'company@tech.com')")
existing = cursor.fetchall()

if existing:
    print(f"Demo accounts already exist, skipping deletion (found {len(existing)} accounts)")
    # Update them instead of recreating
    for user_id, email, role_id in existing:
        if email == 'admin@university.edu':
            cursor.execute("UPDATE users SET is_verified=TRUE WHERE id=%s", (user_id,))
            # Check if admin profile exists
            cursor.execute("SELECT id FROM admins WHERE user_id=%s", (user_id,))
            admin_result = cursor.fetchone()
            if admin_result:
                admin_id = admin_result[0]
                # Ensure verification record exists
                cursor.execute("SELECT id FROM admin_verification WHERE admin_id=%s", (admin_id,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO admin_verification (admin_id, otp_verified) VALUES (%s, TRUE)", (admin_id,))
                else:
                    cursor.execute("UPDATE admin_verification SET otp_verified=TRUE WHERE admin_id=%s", (admin_id,))
                print(f"✓ Admin account updated: {email}")
            else:
                # Create admin profile
                cursor.execute("""
                    INSERT INTO admins (user_id, full_name, email, phone, department)
                    VALUES (%s, 'Admin User', 'admin@university.edu', '9876543200', 'Placement Cell')
                """, (user_id,))
                admin_id = cursor.lastrowid
                cursor.execute("INSERT INTO admin_verification (admin_id, otp_verified) VALUES (%s, TRUE)", (admin_id,))
                print(f"✓ Admin profile created: {email}")
        
        elif email == 'student@university.edu':
            cursor.execute("UPDATE users SET is_verified=TRUE WHERE id=%s", (user_id,))
            # Check if student profile exists
            cursor.execute("SELECT id FROM students WHERE user_id=%s", (user_id,))
            student_result = cursor.fetchone()
            if student_result:
                student_id = student_result[0]
                # Ensure verification record exists
                cursor.execute("SELECT id FROM student_verification WHERE student_id=%s", (student_id,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO student_verification (student_id, otp_verified) VALUES (%s, TRUE)", (student_id,))
                else:
                    cursor.execute("UPDATE student_verification SET otp_verified=TRUE WHERE student_id=%s", (student_id,))
                print(f"✓ Student account updated: {email}")
        
        elif email == 'company@tech.com':
            cursor.execute("UPDATE users SET is_verified=TRUE WHERE id=%s", (user_id,))
            print(f"✓ Company account updated: {email}")
    
    cursor.close()
    conn.close()
    print("\n✅ Demo accounts updated successfully!")
    print("\nLogin credentials:")
    print("━" * 50)
    print("Admin:   admin@university.edu / admin123")
    print("Student: student@university.edu / student123")
    print("Company: company@tech.com / company123")
    print("━" * 50)
    exit(0)

# Insert Admin User
cursor.execute("""
    INSERT INTO users (email, password_hash, role_id, is_verified) 
    VALUES (%s, %s, 3, TRUE)
""", ('admin@university.edu', admin_hash))
admin_user_id = cursor.lastrowid

# Create Admin profile
cursor.execute("""
    INSERT INTO admins (user_id, full_name, email, phone, department)
    VALUES (%s, 'Admin User', 'admin@university.edu', '9876543200', 'Placement Cell')
""", (admin_user_id,))
admin_id = cursor.lastrowid

# Create admin verification record with OTP verified
cursor.execute("""
    INSERT INTO admin_verification (admin_id, otp_verified)
    VALUES (%s, TRUE)
""", (admin_id,))

print(f"✓ Admin account created: admin@university.edu / admin123")

# Insert Student User
cursor.execute("""
    INSERT INTO users (email, password_hash, role_id, is_verified) 
    VALUES (%s, %s, 1, TRUE)
""", ('student@university.edu', student_hash))
student_user_id = cursor.lastrowid

cursor.execute("""
    INSERT INTO students (user_id, full_name, enrollment_number, branch, cgpa, graduation_year, phone, profile_completed) 
    VALUES (%s, 'John Doe', 'EN2024001', 'Computer Science', 8.5, 2026, '9876543210', TRUE)
""", (student_user_id,))
student_id = cursor.lastrowid

# Create student verification record with OTP verified
cursor.execute("""
    INSERT INTO student_verification (student_id, otp_verified)
    VALUES (%s, TRUE)
""", (student_id,))

print(f"✓ Student account created: student@university.edu / student123")

# Insert Company User
cursor.execute("""
    INSERT INTO users (email, password_hash, role_id, is_verified) 
    VALUES (%s, %s, 2, TRUE)
""", ('company@tech.com', company_hash))
company_user_id = cursor.lastrowid

cursor.execute("""
    INSERT INTO companies (user_id, company_name, industry, hr_name, hr_phone, company_website) 
    VALUES (%s, 'TechCorp Solutions', 'Software Development', 'Jane Smith', '9876543211', 'https://techcorp.com')
""", (company_user_id,))
company_id = cursor.lastrowid
print(f"✓ Company account created: company@tech.com / company123")

# Add sample jobs from the company (get first batch for eligible batch)
cursor.execute("SELECT id FROM batches WHERE status='Active' LIMIT 1")
batch_result = cursor.fetchone()
batch_id = batch_result[0] if batch_result else None

cursor.execute("""
    INSERT INTO jobs (company_id, title, job_type, description, requirements, location, salary_range, min_cgpa, eligible_branches, application_deadline, status) 
    VALUES 
    (%s, 'Software Engineering Intern', 'Internship', 'Join our team as a software engineering intern. Work on cutting-edge projects with experienced mentors.', 
     'Python, React, JavaScript basics', 'Bangalore', '₹30,000 - ₹50,000/month', 7.0, 'Computer Science,Information Technology', '2026-06-30', 'Approved'),
    (%s, 'Full Stack Developer', 'Full-Time', 'Looking for passionate full-stack developers to build scalable web applications.', 
     'React, Node.js, MongoDB, 2+ years experience', 'Remote', '₹8-12 LPA', 7.5, 'Computer Science,Information Technology,Electronics', '2026-07-15', 'Approved')
""", (company_id, company_id))
print(f"✓ Sample jobs created")

cursor.close()
conn.close()

print("\n✅ Demo accounts setup complete!")
print("\nLogin credentials:")
print("━" * 50)
print("Admin:   admin@university.edu / admin123")
print("Student: student@university.edu / student123")
print("Company: company@tech.com / company123")
print("━" * 50)
