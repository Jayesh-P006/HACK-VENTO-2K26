import argparse
import json
import os
import random
import sys
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

import pymysql


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


def _table_exists(cur, table: str) -> bool:
    cur.execute("SHOW TABLES LIKE %s", (table,))
    return cur.fetchone() is not None


def _ensure_tables(cur):
    # These tables drive the dashboard stats:
    # - jobs: job posting counts + job types
    # - applications: applicant pipeline
    # - offer_letters: placed students (offer status Sent/Accepted)
    # - departments: branch counts view
    # - placement_stats: cached analytics time series

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS departments (
          id INT NOT NULL AUTO_INCREMENT,
          name VARCHAR(100) NOT NULL,
          code VARCHAR(10) NOT NULL,
          description TEXT NULL,
          total_students INT NOT NULL DEFAULT 0,
          is_active BOOLEAN NOT NULL DEFAULT TRUE,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uq_departments_name (name),
          UNIQUE KEY uq_departments_code (code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
          id INT NOT NULL AUTO_INCREMENT,
          company_id INT NOT NULL,
          title VARCHAR(255) NOT NULL,
          job_type ENUM('Internship','Full-Time','Part-Time') NOT NULL,
          description TEXT NOT NULL,
          requirements TEXT NULL,
          location VARCHAR(255) NULL,
          salary_range VARCHAR(100) NULL,
          min_cgpa DECIMAL(3,2) NOT NULL DEFAULT 0.00,
          eligible_branches TEXT NULL,
          min_10th_percentage DECIMAL(5,2) NULL,
          min_12th_percentage DECIMAL(5,2) NULL,
          application_deadline DATE NOT NULL,
          session_id INT NULL,
          status ENUM('Pending','Approved','Rejected','Closed') NOT NULL DEFAULT 'Pending',
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          KEY idx_jobs_company_id (company_id),
          KEY idx_jobs_status (status),
          CONSTRAINT fk_jobs_company FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )

    # Placement session tables (required by /api/student/jobs)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS placement_sessions (
          id INT NOT NULL AUTO_INCREMENT,
          name VARCHAR(100) NOT NULL,
          description TEXT NULL,
          start_year INT NOT NULL,
          end_year INT NOT NULL,
          start_date DATE NOT NULL,
          end_date DATE NOT NULL,
          status ENUM('Active','Upcoming','Archived') NOT NULL DEFAULT 'Active',
          is_default BOOLEAN NOT NULL DEFAULT FALSE,
          created_by INT NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uq_placement_sessions_name (name),
          KEY idx_placement_sessions_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS batch_session_mapping (
          id INT NOT NULL AUTO_INCREMENT,
          batch_id INT NOT NULL,
          session_id INT NOT NULL,
          is_eligible BOOLEAN NOT NULL DEFAULT TRUE,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY unique_batch_session (batch_id, session_id),
          KEY idx_batch_session_mapping_session_id (session_id),
          CONSTRAINT fk_batch_session_mapping_batch FOREIGN KEY (batch_id) REFERENCES batches (id) ON DELETE CASCADE,
          CONSTRAINT fk_batch_session_mapping_session FOREIGN KEY (session_id) REFERENCES placement_sessions (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
          id INT NOT NULL AUTO_INCREMENT,
          student_id INT NOT NULL,
          job_id INT NOT NULL,
          session_id INT NULL,
          status ENUM('Applied','Shortlisted','Interview','Selected','Rejected') NOT NULL DEFAULT 'Applied',
          applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          notes TEXT NULL,
          PRIMARY KEY (id),
          UNIQUE KEY unique_application (student_id, job_id),
          KEY idx_applications_job_id (job_id),
          KEY idx_applications_student_id (student_id),
          KEY idx_applications_status (status),
          CONSTRAINT fk_applications_student FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
          CONSTRAINT fk_applications_job FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_letters (
          id INT NOT NULL AUTO_INCREMENT,
          application_id INT NOT NULL,
          company_id INT NOT NULL,
          student_id INT NOT NULL,

          designation VARCHAR(255) NOT NULL,
          ctc VARCHAR(100) NOT NULL,
          annual_ctc DECIMAL(12,2) NULL,
          job_location VARCHAR(255) NULL,
          joining_date DATE NULL,
          notice_period INT NULL,

          offer_content TEXT NOT NULL,
          template_used VARCHAR(255) NULL,

          status ENUM('Generated','Sent','Accepted','Rejected','Expired') NOT NULL DEFAULT 'Generated',
          sent_date DATETIME NULL,
          acceptance_date DATETIME NULL,
          expiry_date DATETIME NULL,

          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

          PRIMARY KEY (id),
          KEY idx_offer_letters_company_id (company_id),
          KEY idx_offer_letters_student_id (student_id),
          KEY idx_offer_letters_status (status),
          CONSTRAINT fk_offer_letters_application FOREIGN KEY (application_id) REFERENCES applications (id) ON DELETE CASCADE,
          CONSTRAINT fk_offer_letters_company FOREIGN KEY (company_id) REFERENCES companies (id) ON DELETE CASCADE,
          CONSTRAINT fk_offer_letters_student FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS placement_stats (
          id INT NOT NULL AUTO_INCREMENT,
          date DATE NOT NULL,
          total_students INT NOT NULL DEFAULT 0,
          placed_students INT NOT NULL DEFAULT 0,
          unplaced_students INT NOT NULL DEFAULT 0,
          highest_package DECIMAL(12,2) NOT NULL DEFAULT 0,
          average_package DECIMAL(12,2) NOT NULL DEFAULT 0,
          department_stats JSON NULL,
          total_companies_visiting INT NOT NULL DEFAULT 0,
          companies_in_interview INT NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (id),
          UNIQUE KEY uq_placement_stats_date (date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )


def _seed_departments(cur):
    # Include both short codes and the ones used by our mock student generator.
    departments = [
        ("Computer Science and Engineering", "CSE"),
        ("Information Technology", "IT"),
        ("Electronics and Communication Engineering", "ECE"),
        ("Electrical and Electronics Engineering", "EEE"),
        ("Mechanical Engineering", "ME"),
        ("Mechanical Engineering", "MECH"),
        ("Civil Engineering", "CE"),
        ("Civil Engineering", "CIVIL"),
    ]

    for name, code in departments:
        cur.execute(
            """
            INSERT INTO departments (name, code, description, is_active)
            VALUES (%s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
              description = VALUES(description),
              is_active = TRUE
            """,
            (name, code, name),
        )


def _get_company_ids(cur, *, tag: str) -> List[int]:
    cur.execute(
        """
        SELECT c.id
        FROM companies c
        INNER JOIN users u ON u.id = c.user_id
        WHERE u.email LIKE %s
        ORDER BY c.id ASC
        """,
        (f"company.{tag}.%",),
    )
    return [int(r[0]) for r in cur.fetchall()]


def _get_student_ids(cur, *, tag: str) -> List[int]:
    cur.execute(
        """
        SELECT s.id
        FROM students s
        INNER JOIN users u ON u.id = s.user_id
        WHERE u.email LIKE %s
        ORDER BY s.id ASC
        """,
        (f"student.{tag}.%",),
    )
    return [int(r[0]) for r in cur.fetchall()]


def _random_job_title() -> str:
    roles = [
        "Software Engineer",
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "Data Analyst",
        "ML Engineer",
        "DevOps Engineer",
        "QA Engineer",
    ]
    level = random.choice(["Intern", "Trainee", "Associate", "Junior"])
    role = random.choice(roles)
    return f"{level} {role}" if level != "Intern" else f"{role} Internship"


def _salary_range(job_type: str) -> Tuple[str, float]:
    if job_type == "Internship":
        stipend = random.choice([10000, 15000, 20000, 25000, 30000])
        return f"₹{stipend}/month", float(stipend) * 12
    annual = random.choice([450000, 550000, 650000, 800000, 1000000, 1200000])
    return f"₹{annual/100000:.1f} LPA", float(annual)


def seed_jobs(cur, *, company_ids: Sequence[int], jobs_per_company: int) -> List[int]:
    created_job_ids: List[int] = []
    deadline = date.today() + timedelta(days=30)

    for company_id in company_ids:
        for _ in range(jobs_per_company):
            job_type = random.choice(["Internship", "Full-Time", "Full-Time", "Part-Time"])
            salary_str, _annual = _salary_range(job_type)
            eligible = json.dumps(sorted(random.sample(["CSE", "IT", "ECE", "EEE", "MECH", "CIVIL"], k=3)))

            cur.execute(
                """
                INSERT INTO jobs (
                  company_id, title, job_type, description, requirements,
                  location, salary_range, min_cgpa, eligible_branches,
                  min_10th_percentage, min_12th_percentage, application_deadline,
                                    session_id, status
                ) VALUES (
                  %s, %s, %s, %s, %s,
                  %s, %s, %s, %s,
                                    %s, %s, %s,
                                    %s, 'Approved'
                )
                """,
                (
                    company_id,
                    _random_job_title(),
                    job_type,
                    "Mock job posting for portal testing.",
                    "Strong fundamentals, good communication, and problem-solving skills.",
                    random.choice(["Remote", "Onsite", "Hybrid"]),
                    salary_str,
                    round(random.uniform(6.0, 8.0), 2),
                    eligible,
                    round(random.uniform(70.0, 85.0), 2),
                    round(random.uniform(70.0, 85.0), 2),
                    deadline,
                                        None,
                ),
            )
            created_job_ids.append(int(cur.lastrowid))

    return created_job_ids


def ensure_active_session_and_attach_jobs(cur) -> int:
    """Create an Active placement session if missing and attach any orphan jobs.

    The student jobs endpoint filters by Job.session_id == active_session.id when an Active session exists.
    """
    today = date.today()
    start = today - timedelta(days=30)
    end = today + timedelta(days=120)
    start_year = today.year
    end_year = today.year + 1
    name = f"{start_year}-{str(end_year)[-2:]} Placement Season"

    cur.execute("SELECT id FROM placement_sessions WHERE status='Active' ORDER BY id ASC LIMIT 1")
    row = cur.fetchone()
    if row:
        session_id = int(row[0])
    else:
        cur.execute(
            """
            INSERT INTO placement_sessions (name, description, start_year, end_year, start_date, end_date, status, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, 'Active', TRUE)
            """,
            (
                name,
                "Auto-created mock placement session for portal testing.",
                start_year,
                end_year,
                start,
                end,
            ),
        )
        session_id = int(cur.lastrowid)

    # Attach orphan jobs to the active session and normalize eligible_branches so eligibility parsing works.
    cur.execute(
        """
        UPDATE jobs
        SET session_id = %s
        WHERE session_id IS NULL
        """,
        (session_id,),
    )

    # If eligible_branches looks like JSON (starts with '[') or is NULL/empty, set to 'All'
    cur.execute(
        """
        UPDATE jobs
        SET eligible_branches = 'All'
        WHERE eligible_branches IS NULL
           OR TRIM(eligible_branches) = ''
           OR LEFT(TRIM(eligible_branches), 1) = '['
        """
    )

    return session_id


def seed_applications_and_offers(
    cur,
    *,
    job_ids: Sequence[int],
    student_ids: Sequence[int],
    target_applicants_per_job: Tuple[int, int],
    placed_fraction: float,
) -> Tuple[int, int, int]:
    if not job_ids or not student_ids:
        return 0, 0, 0

    total_applications = 0
    total_selected = 0
    total_offers = 0
    placed_students: set[int] = set()

    status_weights = [
        ("Applied", 0.55),
        ("Shortlisted", 0.2),
        ("Interview", 0.15),
        ("Rejected", 0.07),
        ("Selected", 0.03),
    ]
    statuses = [s for s, _ in status_weights]
    weights = [w for _, w in status_weights]

    for job_id in job_ids:
        applicants = random.randint(*target_applicants_per_job)
        picks = random.sample(student_ids, k=min(applicants, len(student_ids)))
        for student_id in picks:
            status = random.choices(statuses, weights=weights, k=1)[0]
            applied_at = datetime.utcnow() - timedelta(days=random.randint(0, 21))

            try:
                cur.execute(
                    """
                    INSERT INTO applications (student_id, job_id, session_id, status, applied_at, notes)
                    VALUES (%s, %s, NULL, %s, %s, %s)
                    """,
                    (student_id, job_id, status, applied_at.strftime("%Y-%m-%d %H:%M:%S"), "Mock application"),
                )
            except pymysql.err.IntegrityError:
                continue

            application_id = int(cur.lastrowid)
            total_applications += 1

            if status == "Selected":
                total_selected += 1

            # Convert some selected candidates into offers (placed)
            if status == "Selected" and student_id not in placed_students and random.random() < placed_fraction:
                # Need company_id from job
                cur.execute("SELECT company_id, job_type FROM jobs WHERE id=%s", (job_id,))
                row = cur.fetchone()
                if not row:
                    continue
                company_id = int(row[0])
                job_type = str(row[1])

                salary_str, annual_ctc = _salary_range(job_type)
                designation = "Software Engineer" if job_type != "Internship" else "Software Engineering Intern"
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                offer_content = (
                    "Congratulations! You have been selected. "
                    "This is a mock offer letter generated for portal testing." 
                )

                cur.execute(
                    """
                    INSERT INTO offer_letters (
                      application_id, company_id, student_id,
                      designation, ctc, annual_ctc, job_location, joining_date, notice_period,
                      offer_content, template_used,
                      status, sent_date, expiry_date
                    ) VALUES (
                      %s, %s, %s,
                      %s, %s, %s, %s, %s, %s,
                      %s, %s,
                      'Sent', %s, %s
                    )
                    """,
                    (
                        application_id,
                        company_id,
                        student_id,
                        designation,
                        salary_str,
                        annual_ctc,
                        random.choice(["Pune", "Bengaluru", "Hyderabad", "Remote"]),
                        (date.today() + timedelta(days=30)).isoformat(),
                        random.choice([0, 15, 30, 60]),
                        offer_content,
                        "mock-template",
                        now,
                        (date.today() + timedelta(days=15)).isoformat() + " 00:00:00",
                    ),
                )

                placed_students.add(student_id)
                total_offers += 1

    return total_applications, total_selected, total_offers


def upsert_placement_stats(cur) -> Dict[str, int]:
    today = date.today().isoformat()

    cur.execute("SELECT COUNT(*) FROM students")
    total_students = int(cur.fetchone()[0])

    cur.execute(
        """
        SELECT COUNT(DISTINCT student_id)
        FROM offer_letters
        WHERE status IN ('Sent','Accepted')
        """
    )
    placed_students = int(cur.fetchone()[0])
    unplaced_students = max(0, total_students - placed_students)

    cur.execute(
        """
        SELECT COALESCE(MAX(annual_ctc), 0), COALESCE(AVG(annual_ctc), 0)
        FROM offer_letters
        WHERE status IN ('Sent','Accepted')
        """
    )
    highest, avg = cur.fetchone()
    highest = float(highest or 0)
    avg = float(avg or 0)

    # Department stats: count totals per branch value as stored in students.branch
    cur.execute(
        """
        SELECT s.branch AS branch, COUNT(*) AS total
        FROM students s
        GROUP BY s.branch
        """
    )
    totals_by_branch = {str(b): int(t) for b, t in cur.fetchall()}

    cur.execute(
        """
        SELECT s.branch AS branch, COUNT(DISTINCT o.student_id) AS placed
        FROM offer_letters o
        INNER JOIN students s ON s.id = o.student_id
        WHERE o.status IN ('Sent','Accepted')
        GROUP BY s.branch
        """
    )
    placed_by_branch = {str(b): int(p) for b, p in cur.fetchall()}

    department_stats = {
        branch: {
            "total": totals_by_branch.get(branch, 0),
            "placed": placed_by_branch.get(branch, 0),
        }
        for branch in sorted(totals_by_branch.keys())
    }

    cur.execute(
        """
        INSERT INTO placement_stats (
          date, total_students, placed_students, unplaced_students,
          highest_package, average_package, department_stats,
          total_companies_visiting, companies_in_interview
        ) VALUES (
          %s, %s, %s, %s,
          %s, %s, %s,
          %s, %s
        )
        ON DUPLICATE KEY UPDATE
          total_students=VALUES(total_students),
          placed_students=VALUES(placed_students),
          unplaced_students=VALUES(unplaced_students),
          highest_package=VALUES(highest_package),
          average_package=VALUES(average_package),
          department_stats=VALUES(department_stats)
        """,
        (
            today,
            total_students,
            placed_students,
            unplaced_students,
            highest,
            avg,
            json.dumps(department_stats),
            0,
            0,
        ),
    )

    return {
        "total_students": total_students,
        "placed_students": placed_students,
        "unplaced_students": unplaced_students,
    }


def main():
    parser = argparse.ArgumentParser(description="Seed jobs, applications, and offer letters for mock portal analytics")
    parser.add_argument("--tag", type=str, default=os.getenv("MOCK_TAG", "mock"))
    parser.add_argument("--jobs-per-company", type=int, default=3)
    parser.add_argument("--applicants-min", type=int, default=8)
    parser.add_argument("--applicants-max", type=int, default=20)
    parser.add_argument(
        "--placed-fraction",
        type=float,
        default=0.65,
        help="Probability that a Selected application gets an offer letter (placed).",
    )
    parser.add_argument("--clear", action="store_true", help="Delete jobs/applications/offers for companies of this tag")

    args = parser.parse_args()

    if args.applicants_min < 1 or args.applicants_max < args.applicants_min:
        raise SystemExit("Invalid applicants range")

    conn = _connect()
    try:
        with conn.cursor() as cur:
            _ensure_tables(cur)
            _seed_departments(cur)

            company_ids = _get_company_ids(cur, tag=args.tag)
            student_ids = _get_student_ids(cur, tag=args.tag)

            if not company_ids:
                raise SystemExit(f"No mock companies found for tag={args.tag}. Seed companies first.")
            if not student_ids:
                raise SystemExit(f"No mock students found for tag={args.tag}. Seed students first.")

            if args.clear:
                # Remove offers/applications/jobs belonging to these companies
                cur.execute(
                    """
                    DELETE o FROM offer_letters o
                    INNER JOIN jobs j ON j.company_id = o.company_id
                    WHERE j.company_id IN (%s)
                    """.replace("%s", ",".join(["%s"] * len(company_ids))),
                    tuple(company_ids),
                )
                cur.execute(
                    """
                    DELETE a FROM applications a
                    INNER JOIN jobs j ON j.id = a.job_id
                    WHERE j.company_id IN (%s)
                    """.replace("%s", ",".join(["%s"] * len(company_ids))),
                    tuple(company_ids),
                )
                cur.execute(
                    """
                    DELETE FROM jobs WHERE company_id IN (%s)
                    """.replace("%s", ",".join(["%s"] * len(company_ids))),
                    tuple(company_ids),
                )

            job_ids = seed_jobs(cur, company_ids=company_ids, jobs_per_company=args.jobs_per_company)

            session_id = ensure_active_session_and_attach_jobs(cur)

            apps, selected, offers = seed_applications_and_offers(
                cur,
                job_ids=job_ids,
                student_ids=student_ids,
                target_applicants_per_job=(args.applicants_min, args.applicants_max),
                placed_fraction=max(0.0, min(1.0, args.placed_fraction)),
            )

            stats = upsert_placement_stats(cur)

            print("\n✅ Mock activity seeded")
            print(f"- Tag: {args.tag}")
            print(f"- Jobs created: {len(job_ids)}")
            print(f"- Active session id: {session_id}")
            print(f"- Applications created: {apps}")
            print(f"- Selected applications: {selected}")
            print(f"- Offer letters created (placed): {offers}")
            print("\n📊 Placement stats (today)")
            print(f"- Total students: {stats['total_students']}")
            print(f"- Placed students: {stats['placed_students']}")
            print(f"- Unplaced students: {stats['unplaced_students']}")

    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
