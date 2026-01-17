import argparse
import os
import random
import sys
from datetime import datetime
from typing import Optional

# Ensure backend imports work when running from repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash

from app import app, db
from models import Company, Student, StudentVerification, User


BRANCHES = ["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"]
INDUSTRIES = [
    "IT Services",
    "Software",
    "FinTech",
    "EdTech",
    "HealthTech",
    "E-commerce",
    "AI/ML",
    "Cybersecurity",
    "Cloud",
    "Consulting",
]

FIRST_NAMES = [
    "Aarav",
    "Vivaan",
    "Aditya",
    "Arjun",
    "Sai",
    "Ishaan",
    "Rohan",
    "Aryan",
    "Krishna",
    "Dhruv",
    "Aadhya",
    "Ananya",
    "Diya",
    "Isha",
    "Kavya",
    "Kiara",
    "Mira",
    "Navya",
    "Saanvi",
    "Sara",
    "Anika",
    "Priya",
    "Riya",
    "Sneha",
    "Pooja",
    "Neha",
    "Raj",
    "Amit",
    "Rahul",
    "Karan",
    "Varun",
    "Nikhil",
]

LAST_NAMES = [
    "Sharma",
    "Patel",
    "Kumar",
    "Singh",
    "Gupta",
    "Mehta",
    "Reddy",
    "Rao",
    "Verma",
    "Joshi",
    "Iyer",
    "Nair",
    "Agarwal",
    "Kapoor",
    "Malhotra",
    "Desai",
    "Pandey",
    "Mishra",
    "Trivedi",
    "Shah",
]

SKILLS_POOL = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "Flask",
    "Django",
    "FastAPI",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "AWS",
    "Docker",
    "Kubernetes",
    "Git",
    "REST API",
    "GraphQL",
    "CI/CD",
    "Data Structures",
    "Machine Learning",
]


def _rand_phone() -> str:
    return f"+91{random.randint(7000000000, 9999999999)}"


def _pick_skills() -> str:
    return ", ".join(sorted(random.sample(SKILLS_POOL, k=random.randint(5, 9))))


def _ensure_student_verification(student_id: int, *, admin_user_id: Optional[int]):
    now = datetime.utcnow()
    rec = StudentVerification.query.filter_by(student_id=student_id).first()
    if not rec:
        rec = StudentVerification(student_id=student_id)
        db.session.add(rec)
        db.session.flush()

    rec.status = "Verified"
    rec.otp = "000000"
    rec.otp_verified = True
    rec.otp_sent_at = now
    rec.otp_verified_at = now
    rec.otp_attempts = 0
    rec.verification_date = now
    rec.verified_by = admin_user_id

    # Optional document URLs (placeholders)
    rec.marksheet_10th_url = rec.marksheet_10th_url or "https://example.com/mock/10th.pdf"
    rec.marksheet_12th_url = rec.marksheet_12th_url or "https://example.com/mock/12th.pdf"
    rec.degree_certificate_url = rec.degree_certificate_url or "https://example.com/mock/degree.pdf"


def clear_mock(*, tag: str):
    """Delete previously seeded mock users by tag."""
    # Email patterns
    student_pat = f"student.%{tag}%@university.edu"
    company_pat = f"company.%{tag}%@company.com"

    users = (
        User.query.filter(
            (User.email.like(student_pat)) | (User.email.like(company_pat))
        )
        .all()
    )

    for user in users:
        # Relationships are configured with cascades, but StudentVerification is not a child of User.
        if user.student:
            StudentVerification.query.filter_by(student_id=user.student.id).delete()
        db.session.delete(user)

    db.session.commit()


def seed_students(*, count: int, tag: str, password: str, admin_user_id: Optional[int]):
    password_hash = generate_password_hash(password)

    created = 0
    i = 1
    while created < count:
        email = f"student.{tag}.{i}@university.edu"
        if User.query.filter_by(email=email).first():
            i += 1
            continue

        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        branch = random.choice(BRANCHES)

        user = User(email=email, role_id=1, is_verified=True, password_hash=password_hash)
        db.session.add(user)
        db.session.flush()

        grad_year = random.choice([2026, 2027, 2028])
        current_year = max(1, min(4, 2026 - grad_year + 4))

        enrollment = f"MOCK{tag.upper()}{grad_year}{i:04d}"
        # Ensure unique enrollment
        while Student.query.filter_by(enrollment_number=enrollment).first():
            enrollment = f"MOCK{tag.upper()}{grad_year}{random.randint(1, 9999):04d}"

        student = Student(
            user_id=user.id,
            full_name=f"{first} {last}",
            enrollment_number=enrollment,
            branch=branch,
            cgpa=round(random.uniform(6.5, 9.8), 2),
            tenth_percentage=round(random.uniform(72.0, 98.0), 2),
            twelfth_percentage=round(random.uniform(70.0, 97.0), 2),
            graduation_year=grad_year,
            current_year=current_year,
            phone=_rand_phone(),
            skills=_pick_skills(),
            experience=random.choice(
                [
                    "",
                    "Software Intern (3 months)",
                    "Web Developer Intern (2 months)",
                    "Data Analyst Intern (4 months)",
                ]
            ),
            projects=random.choice(
                [
                    "Portfolio Website (React)",
                    "E-commerce App (MERN)",
                    "Campus Placement Portal (Flask)",
                    "ATS Resume Analyzer (Python)",
                ]
            ),
            certifications=random.choice(
                [
                    "",
                    "AWS Cloud Practitioner",
                    "Google Data Analytics",
                    "Meta Frontend",
                ]
            ),
            linkedin_url=f"https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(100,999)}",
            github_url=f"https://github.com/{first.lower()}{last.lower()}{random.randint(10,99)}",
            profile_completed=True,
        )
        db.session.add(student)
        db.session.flush()

        _ensure_student_verification(student.id, admin_user_id=admin_user_id)

        created += 1
        i += 1

        # Commit in batches
        if created % 25 == 0:
            db.session.commit()

    db.session.commit()
    return created


def seed_companies(*, count: int, tag: str, password: str):
    password_hash = generate_password_hash(password)

    created = 0
    i = 1
    while created < count:
        email = f"company.{tag}.{i}@company.com"
        if User.query.filter_by(email=email).first():
            i += 1
            continue

        company_name = f"{random.choice(['Tech', 'Data', 'Cloud', 'Nova', 'Next', 'Blue', 'Apex'])}{random.choice(['Labs', 'Systems', 'Solutions', 'Works', 'Dynamics', 'Soft'])} {i}"
        hr_first = random.choice(FIRST_NAMES)
        hr_last = random.choice(LAST_NAMES)

        user = User(email=email, role_id=2, is_verified=True, password_hash=password_hash)
        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.id,
            company_name=company_name,
            industry=random.choice(INDUSTRIES),
            hr_name=f"{hr_first} {hr_last}",
            hr_phone=_rand_phone(),
            company_website=f"https://{company_name.lower().replace(' ', '')}.com",
            logo_url="https://dummyimage.com/256x256/4f46e5/ffffff.png&text=Logo",
            description=f"{company_name} is a mock company used for portal testing.",
        )
        db.session.add(company)

        created += 1
        i += 1

        if created % 10 == 0:
            db.session.commit()

    db.session.commit()
    return created


def main():
    parser = argparse.ArgumentParser(description="Seed mock students/companies for portal testing")
    parser.add_argument("--students", type=int, default=50)
    parser.add_argument("--companies", type=int, default=10)
    parser.add_argument("--tag", type=str, default=os.getenv("MOCK_TAG", "mock"))
    parser.add_argument("--student-password", type=str, default=os.getenv("MOCK_STUDENT_PASSWORD", "student123"))
    parser.add_argument("--company-password", type=str, default=os.getenv("MOCK_COMPANY_PASSWORD", "company123"))
    parser.add_argument("--clear", action="store_true", help="Delete previously seeded mock users for this tag")

    args = parser.parse_args()

    with app.app_context():
        # Best-effort: use an existing admin user for verified_by
        admin_user = User.query.filter_by(role_id=3).first()
        admin_user_id = admin_user.id if admin_user else None

        if args.clear:
            clear_mock(tag=args.tag)

        created_companies = seed_companies(count=args.companies, tag=args.tag, password=args.company_password)
        created_students = seed_students(
            count=args.students,
            tag=args.tag,
            password=args.student_password,
            admin_user_id=admin_user_id,
        )

        print("\n✅ Mock data seeded")
        print(f"- Companies created: {created_companies}")
        print(f"- Students created: {created_students}")
        print(f"- Tag: {args.tag}")
        print("\nLogin examples:")
        print(f"- Student: student.{args.tag}.1@university.edu / {args.student_password}")
        print(f"- Company: company.{args.tag}.1@company.com / {args.company_password}")


if __name__ == "__main__":
    main()
