import argparse
import os
import random
import re
import sys
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

import pymysql
from werkzeug.security import generate_password_hash


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


def _parse_mysql_url(url: str) -> Tuple[str, str, str, str, int]:
    parsed = urlparse(url)
    if parsed.scheme not in ("mysql", "mysql+pymysql"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    host = parsed.hostname
    port = parsed.port or 3306
    user = parsed.username
    password = parsed.password or ""
    database = (parsed.path or "").lstrip("/")
    if not host or not user or not database:
        raise ValueError("Invalid MYSQL URL")
    return host, user, password, database, port


def _get_env(name: str, fallbacks=()):
    v = os.getenv(name)
    if v:
        return v
    for fb in fallbacks:
        v = os.getenv(fb)
        if v:
            return v
    return None


def _db_config_from_env() -> Tuple[str, str, str, str, int]:
    # Prefer Railway public URL for local runs.
    mysql_public_url = _get_env("MYSQL_PUBLIC_URL")
    if mysql_public_url:
        try:
            return _parse_mysql_url(mysql_public_url)
        except Exception:
            pass

    host = _get_env("MYSQLHOST", ("DB_HOST",))
    user = _get_env("MYSQLUSER", ("DB_USER",))
    password = _get_env("MYSQLPASSWORD", ("DB_PASSWORD",))
    database = _get_env("MYSQLDATABASE", ("DB_NAME",))
    port = _get_env("MYSQLPORT", ("DB_PORT",))

    if host and host.endswith(".railway.internal"):
        proxy_host = _get_env("RAILWAY_TCP_PROXY_DOMAIN")
        proxy_port = _get_env("RAILWAY_TCP_PROXY_PORT")
        if proxy_host and proxy_port:
            host = proxy_host
            port = proxy_port

    if not host or not user or not database:
        missing = [
            k
            for k, v in {
                "MYSQLHOST/DB_HOST": host,
                "MYSQLUSER/DB_USER": user,
                "MYSQLPASSWORD/DB_PASSWORD": password,
                "MYSQLDATABASE/DB_NAME": database,
            }.items()
            if not v
        ]
        raise SystemExit(
            "Missing required DB env vars: "
            + ", ".join(missing)
            + "\nTip: run via `railway run ...` so env vars are injected."
        )

    try:
        port_i = int(port) if port else 3306
    except ValueError:
        port_i = 3306

    return host, user, password or "", database, port_i


def _connect():
    host, user, password, database, port = _db_config_from_env()
    print(f"Connecting to MySQL at {host}:{port}, db={database}...")
    return pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        autocommit=True,
        charset="utf8mb4",
        connect_timeout=15,
        read_timeout=60,
        write_timeout=60,
    )


def _is_lost_connection(exc: Exception) -> bool:
    if not isinstance(exc, pymysql.MySQLError):
        return False
    code = exc.args[0] if exc.args else None
    # 2006: MySQL server has gone away, 2013: Lost connection during query
    return code in (2006, 2013)


def _exec(cur, sql: str, params=None, *, retries: int = 3):
    """Execute with retry for flaky proxy connections."""
    attempt = 0
    while True:
        try:
            return cur.execute(sql, params)
        except Exception as e:
            attempt += 1
            if attempt <= retries and _is_lost_connection(e):
                raise  # handled by reconnect loop in main
            raise


def _find_admin_user_id(cur) -> Optional[int]:
    _exec(cur, "SELECT id FROM users WHERE role_id = 3 ORDER BY id ASC LIMIT 1")
    row = cur.fetchone()
    return int(row[0]) if row else None


def clear_mock(cur, *, tag: str):
    student_like = f"student.{tag}.%"
    company_like = f"company.{tag}.%"

    # Delete student_verification for matched students
    _exec(
        cur,
        """
        DELETE sv
        FROM student_verification sv
        INNER JOIN students s ON s.id = sv.student_id
        INNER JOIN users u ON u.id = s.user_id
        WHERE u.email LIKE %s
        """,
        (student_like,),
    )

    # Delete students (cascades user via FK users->students is on students.user_id, so delete users instead)
    # Delete companies similarly by deleting users.
    _exec(
        cur,
        "DELETE FROM users WHERE email LIKE %s OR email LIKE %s",
        (student_like, company_like),
    )


def _email_exists(cur, email: str) -> bool:
    _exec(cur, "SELECT 1 FROM users WHERE email=%s LIMIT 1", (email,))
    return cur.fetchone() is not None


def _enrollment_exists(cur, enrollment: str) -> bool:
    _exec(cur, "SELECT 1 FROM students WHERE enrollment_number=%s LIMIT 1", (enrollment,))
    return cur.fetchone() is not None


def seed_companies(cur, *, count: int, tag: str, password: str) -> int:
    password_hash = generate_password_hash(password)

    created = 0
    i = 1
    while created < count:
        email = f"company.{tag}.{i}@company.com"
        if _email_exists(cur, email):
            i += 1
            continue

        company_name = (
            f"{random.choice(['Tech', 'Data', 'Cloud', 'Nova', 'Next', 'Blue', 'Apex'])}"
            f"{random.choice(['Labs', 'Systems', 'Solutions', 'Works', 'Dynamics', 'Soft'])} {i}"
        )
        hr_first = random.choice(FIRST_NAMES)
        hr_last = random.choice(LAST_NAMES)

        # users
        _exec(
            cur,
            """
            INSERT INTO users (email, password_hash, role_id, is_verified)
            VALUES (%s, %s, 2, TRUE)
            """,
            (email, password_hash),
        )
        user_id = cur.lastrowid

        # companies
        _exec(
            cur,
            """
            INSERT INTO companies
              (user_id, company_name, industry, hr_name, hr_phone, company_website, logo_url, description)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                company_name,
                random.choice(INDUSTRIES),
                f"{hr_first} {hr_last}",
                _rand_phone(),
                f"https://{company_name.lower().replace(' ', '')}.com",
                "https://dummyimage.com/256x256/4f46e5/ffffff.png&text=Logo",
                f"{company_name} is a mock company used for portal testing.",
            ),
        )

        created += 1
        i += 1

    return created


def seed_students(cur, *, count: int, tag: str, password: str, admin_user_id: Optional[int]) -> int:
    password_hash = generate_password_hash(password)

    created = 0
    i = 1
    while created < count:
        email = f"student.{tag}.{i}@university.edu"
        if _email_exists(cur, email):
            i += 1
            continue

        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        branch = random.choice(BRANCHES)

        grad_year = random.choice([2026, 2027, 2028])
        current_year = max(1, min(4, 2026 - grad_year + 4))

        enrollment = f"MOCK{tag.upper()}{grad_year}{i:04d}"
        while _enrollment_exists(cur, enrollment):
            enrollment = f"MOCK{tag.upper()}{grad_year}{random.randint(1, 9999):04d}"

        # users
        _exec(
            cur,
            """
            INSERT INTO users (email, password_hash, role_id, is_verified)
            VALUES (%s, %s, 1, TRUE)
            """,
            (email, password_hash),
        )
        user_id = cur.lastrowid

        # students
        _exec(
            cur,
            """
            INSERT INTO students (
              user_id, full_name, enrollment_number, branch, cgpa,
              tenth_percentage, twelfth_percentage, graduation_year, current_year,
              phone, skills, experience, projects, certifications,
              linkedin_url, github_url, profile_completed
            ) VALUES (
              %s, %s, %s, %s, %s,
              %s, %s, %s, %s,
              %s, %s, %s, %s, %s,
              %s, %s, TRUE
            )
            """,
            (
                user_id,
                f"{first} {last}",
                enrollment,
                branch,
                round(random.uniform(6.5, 9.8), 2),
                round(random.uniform(72.0, 98.0), 2),
                round(random.uniform(70.0, 97.0), 2),
                grad_year,
                current_year,
                _rand_phone(),
                _pick_skills(),
                random.choice(
                    [
                        "",
                        "Software Intern (3 months)",
                        "Web Developer Intern (2 months)",
                        "Data Analyst Intern (4 months)",
                    ]
                ),
                random.choice(
                    [
                        "Portfolio Website (React)",
                        "E-commerce App (MERN)",
                        "Campus Placement Portal (Flask)",
                        "ATS Resume Analyzer (Python)",
                    ]
                ),
                random.choice(["", "AWS Cloud Practitioner", "Google Data Analytics", "Meta Frontend"]),
                f"https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(100,999)}",
                f"https://github.com/{first.lower()}{last.lower()}{random.randint(10,99)}",
            ),
        )
        student_id = cur.lastrowid

        # student_verification
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        _exec(
            cur,
            """
            INSERT INTO student_verification (
              student_id, status,
              otp, otp_verified, otp_sent_at, otp_verified_at, otp_attempts,
              marksheet_10th_url, marksheet_12th_url, degree_certificate_url,
              verification_date, verified_by, submitted_at
            ) VALUES (
              %s, 'Verified',
              '000000', TRUE, %s, %s, 0,
              %s, %s, %s,
              %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
              status='Verified',
              otp='000000',
              otp_verified=TRUE,
              otp_sent_at=VALUES(otp_sent_at),
              otp_verified_at=VALUES(otp_verified_at),
              otp_attempts=0,
              verification_date=VALUES(verification_date),
              verified_by=VALUES(verified_by)
            """,
            (
                student_id,
                now,
                now,
                "https://example.com/mock/10th.pdf",
                "https://example.com/mock/12th.pdf",
                "https://example.com/mock/degree.pdf",
                now,
                admin_user_id,
                now,
            ),
        )

        created += 1
        i += 1

    return created


def main():
    parser = argparse.ArgumentParser(description="Seed mock students/companies directly via SQL (Railway-friendly)")
    parser.add_argument("--students", type=int, default=50)
    parser.add_argument("--companies", type=int, default=10)
    parser.add_argument("--tag", type=str, default=os.getenv("MOCK_TAG", "mock"))
    parser.add_argument(
        "--student-password",
        type=str,
        default=os.getenv("MOCK_STUDENT_PASSWORD", "student123"),
    )
    parser.add_argument(
        "--company-password",
        type=str,
        default=os.getenv("MOCK_COMPANY_PASSWORD", "company123"),
    )
    parser.add_argument("--clear", action="store_true", help="Delete previously seeded mock users for this tag")

    args = parser.parse_args()

    # Railway's public proxy can occasionally drop connections from Windows.
    # We'll reconnect and re-run once if we hit a lost-connection error.
    attempts = 0
    while True:
        attempts += 1
        conn = _connect()
        try:
            with conn.cursor() as cur:
                admin_user_id = _find_admin_user_id(cur)

                if args.clear:
                    clear_mock(cur, tag=args.tag)

                created_companies = seed_companies(
                    cur, count=args.companies, tag=args.tag, password=args.company_password
                )
                created_students = seed_students(
                    cur,
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
            return
        except Exception as e:
            if attempts < 3 and _is_lost_connection(e):
                try:
                    conn.close()
                except Exception:
                    pass
                print("[warn] Lost connection to MySQL proxy; retrying...")
                continue
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
