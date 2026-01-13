#!/usr/bin/env python3
"""
Create demo accounts and data
"""
import pymysql
import os
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'placement_portal')

try:
    print("Connecting to database...")
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        autocommit=True
    )
    cursor = conn.cursor()
    
    # Create demo users
    demo_users = [
        ('admin@university.edu', generate_password_hash('admin123'), 'Admin User', 'admin'),
        ('student@university.edu', generate_password_hash('student123'), 'Demo Student', 'student'),
        ('company@tech.com', generate_password_hash('company123'), 'Tech Company', 'company'),
    ]
    
    print("\nCreating demo users...")
    for email, password_hash, name, role in demo_users:
        try:
            cursor.execute("""
                INSERT INTO users (email, password, name, role, is_verified, created_at)
                VALUES (%s, %s, %s, %s, 1, NOW())
            """, (email, password_hash, name, role))
            print(f"✓ Created {role}: {email}")
        except Exception as e:
            if 'Duplicate entry' in str(e):
                print(f"⚠ Already exists: {email}")
            else:
                print(f"✗ Error creating {email}: {str(e)[:100]}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Demo data created successfully!")
    print("\nYou can now login with:")
    print("  Admin: admin@university.edu / admin123")
    print("  Student: student@university.edu / student123")
    print("  Company: company@tech.com / company123")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
