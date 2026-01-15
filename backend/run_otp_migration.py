import os
import pathlib
from urllib.parse import urlparse
import pymysql
from pymysql.err import OperationalError

SQL_PATH = pathlib.Path(__file__).resolve().parents[1] / "database" / "otp_columns.sql"

public_url = os.environ.get("MYSQL_PUBLIC_URL")
if not public_url:
    raise SystemExit("MYSQL_PUBLIC_URL not set")

u = urlparse(public_url)
conn = pymysql.connect(
    host=u.hostname,
    port=u.port or 3306,
    user=u.username,
    password=u.password,
    database=u.path.lstrip("/"),
    charset="utf8mb4",
)

sql = SQL_PATH.read_text()
cur = conn.cursor()

def table_exists(table_name):
    cur.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """,
        (u.path.lstrip("/"), table_name),
    )
    return cur.fetchone()[0] > 0

if not table_exists("admin_verification"):
    if not table_exists("admins"):
        create_admins_sql = """
        CREATE TABLE IF NOT EXISTS admins (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL UNIQUE,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone VARCHAR(15),
            department VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
        cur.execute(create_admins_sql)

    create_admin_verification_sql = """
    CREATE TABLE IF NOT EXISTS admin_verification (
        id INT PRIMARY KEY AUTO_INCREMENT,
        admin_id INT NOT NULL UNIQUE,
        status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
        otp VARCHAR(6),
        otp_verified BOOLEAN DEFAULT FALSE,
        otp_sent_at DATETIME,
        otp_verified_at DATETIME,
        otp_attempts INT DEFAULT 0,
        verification_date TIMESTAMP NULL,
        approved_by INT,
        rejection_reason TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """
    cur.execute(create_admin_verification_sql)

for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
    try:
        cur.execute(stmt)
    except OperationalError as e:
        if e.args and e.args[0] in (1060, 1146):
            # Duplicate column - already applied
            # Missing table - skip
            continue
        raise

conn.commit()
conn.close()
print("OTP columns applied (existing columns skipped)")
