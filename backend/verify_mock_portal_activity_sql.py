import os
import sys
from urllib.parse import urlparse

import pymysql


def _parse_mysql_url(url: str):
    p = urlparse(url)
    host = p.hostname
    port = p.port or 3306
    user = p.username
    password = p.password or ""
    database = (p.path or "").lstrip("/")
    if not host or not user or not database:
        raise SystemExit("Invalid MYSQL url")
    return host, port, user, password, database


def _connect():
    url = os.environ.get("MYSQL_PUBLIC_URL") or os.environ.get("MYSQL_URL")
    if not url:
        raise SystemExit("Missing MYSQL_PUBLIC_URL/MYSQL_URL (run with `railway run`) ")
    host, port, user, password, database = _parse_mysql_url(url)
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        autocommit=True,
    )


def main():
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            users = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM students")
            students = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM companies")
            companies = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM jobs")
            jobs = int(cur.fetchone()[0])
            cur.execute("SELECT job_type, COUNT(*) FROM jobs GROUP BY job_type")
            job_types = cur.fetchall()
            cur.execute("SELECT COUNT(*) FROM jobs WHERE status='Approved'")
            jobs_approved = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM jobs WHERE session_id IS NULL")
            jobs_no_session = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM applications")
            applications = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM offer_letters")
            offers = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM offer_letters WHERE status IN ('Sent','Accepted')")
            offers_sent = int(cur.fetchone()[0])
            cur.execute("SELECT date,total_students,placed_students,unplaced_students FROM placement_stats ORDER BY date DESC LIMIT 1")
            latest_stats = cur.fetchone()

        print("✅ DB counts")
        print("- users:", users)
        print("- students:", students)
        print("- companies:", companies)
        print("- jobs:", jobs)
        print("- jobs approved:", jobs_approved)
        print("- jobs without session_id:", jobs_no_session)
        print("- jobs by type:", job_types)
        print("- applications:", applications)
        print("- offer_letters:", offers, "(Sent/Accepted:", offers_sent, ")")
        print("- latest placement_stats:", latest_stats)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
