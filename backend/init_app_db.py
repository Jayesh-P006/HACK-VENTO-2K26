#!/usr/bin/env python3
"""
Initialize database using Flask ORM
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from models import User
from dotenv import load_dotenv

load_dotenv()

# Role mapping
ROLES = {
    'student': 1,
    'company': 2,
    'admin': 3
}

def init_db():
    """Initialize database with Flask ORM"""
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("✓ Tables created")
        
        print("\nCreating demo users...")
        
        demo_accounts = [
            {
                'email': 'admin@university.edu',
                'password': 'admin123',
                'role': 'admin'
            },
            {
                'email': 'student@university.edu',
                'password': 'student123',
                'role': 'student'
            },
            {
                'email': 'company@tech.com',
                'password': 'company123',
                'role': 'company'
            }
        ]
        
        for account in demo_accounts:
            # Check if user already exists
            existing = User.query.filter_by(email=account['email']).first()
            if existing:
                print(f"⚠ Already exists: {account['email']}")
                continue
            
            user = User(
                email=account['email'],
                role_id=ROLES[account['role']],
                is_verified=True
            )
            user.set_password(account['password'])
            
            db.session.add(user)
            print(f"✓ Created {account['role']}: {account['email']}")
        
        try:
            db.session.commit()
            print("\n✅ Database initialized successfully!")
            print("\nYou can now login with:")
            for account in demo_accounts:
                print(f"  {account['role'].capitalize()}: {account['email']} / {account['password']}")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error: {e}")

if __name__ == '__main__':
    init_db()
