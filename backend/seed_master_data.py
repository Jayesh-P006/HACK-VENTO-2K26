"""
Seed default master data for the placement portal
This script populates:
- Branches/Departments
- Academic Batches
- Default Skills
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

from app import app, db
from models import Department, Batch, Skill

def seed_departments():
    """Seed default branches/departments"""
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
        existing = Department.query.filter_by(name=branch['name']).first()
        if not existing:
            dept = Department(
                name=branch['name'],
                full_name=branch['full_name']
            )
            db.session.add(dept)
            print(f"✓ Added department: {branch['name']}")
        else:
            print(f"  Department already exists: {branch['name']}")
    
    db.session.commit()

def seed_batches():
    """Seed default academic batches"""
    batches = [
        {
            'batch_code': '2023-27',
            'start_year': 2023,
            'end_year': 2027,
            'degree': 'B.Tech',
            'program': 'All',
            'status': 'Active'
        },
        {
            'batch_code': '2022-26',
            'start_year': 2022,
            'end_year': 2026,
            'degree': 'B.Tech',
            'program': 'All',
            'status': 'Active'
        },
        {
            'batch_code': '2021-25',
            'start_year': 2021,
            'end_year': 2025,
            'degree': 'B.Tech',
            'program': 'All',
            'status': 'Active'
        },
        {
            'batch_code': '2020-24',
            'start_year': 2020,
            'end_year': 2024,
            'degree': 'B.Tech',
            'program': 'All',
            'status': 'Graduated'
        },
    ]
    
    for batch in batches:
        existing = Batch.query.filter_by(batch_code=batch['batch_code']).first()
        if not existing:
            new_batch = Batch(
                batch_code=batch['batch_code'],
                start_year=batch['start_year'],
                end_year=batch['end_year'],
                degree=batch['degree'],
                program=batch['program'],
                status=batch['status']
            )
            db.session.add(new_batch)
            print(f"✓ Added batch: {batch['batch_code']}")
        else:
            print(f"  Batch already exists: {batch['batch_code']}")
    
    db.session.commit()

def seed_skills():
    """Seed default skills"""
    skills = [
        'Python', 'Java', 'C++', 'JavaScript', 'TypeScript',
        'SQL', 'HTML', 'CSS', 'React', 'Node.js',
        'Django', 'Flask', 'Spring Boot', 'MongoDB', 'PostgreSQL',
        'AWS', 'Docker', 'Kubernetes', 'Git', 'REST API',
        'Microservices', 'Machine Learning', 'Data Analysis', 'Problem Solving', 'Communication'
    ]
    
    for skill in skills:
        existing = Skill.query.filter_by(skill_name=skill).first()
        if not existing:
            new_skill = Skill(skill_name=skill)
            db.session.add(new_skill)
            print(f"✓ Added skill: {skill}")
        else:
            print(f"  Skill already exists: {skill}")
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        print("\n🌱 Seeding master data...\n")
        print("📚 Seeding departments...")
        seed_departments()
        print("\n📅 Seeding batches...")
        seed_batches()
        print("\n💻 Seeding skills...")
        seed_skills()
        print("\n✅ Master data seeding complete!\n")
