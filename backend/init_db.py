import pymysql
from pathlib import Path

SCHEMA_PATH = Path(r"c:\Jayesh\Placement and Intership portal\database\schema.sql")

sql_text = SCHEMA_PATH.read_text(encoding="utf-8")

statements = []
chunk = []
for line in sql_text.splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith('--'):
        continue
    chunk.append(line)
    if stripped.endswith(';'):
        statements.append('\n'.join(chunk))
        chunk = []
if chunk:
    statements.append('\n'.join(chunk))

# Skip database directives in file; we'll handle explicitly
statements = [s for s in statements if not s.lower().startswith("create database") and not s.lower().startswith("use ")]

# Ensure database exists
bootstrap = pymysql.connect(host="localhost", user="root", password="jpassword", autocommit=True)
with bootstrap.cursor() as cur:
    cur.execute("CREATE DATABASE IF NOT EXISTS placement_portal;")
bootstrap.close()

# Now operate inside the DB
conn = pymysql.connect(host="localhost", user="root", password="jpassword", database="placement_portal", autocommit=True)
cur = conn.cursor()

# Ensure views can be recreated if script ran before
cur.execute("DROP VIEW IF EXISTS placement_stats;")
cur.execute("DROP VIEW IF EXISTS branch_placement;")

for stmt in statements:
    cur.execute(stmt)
cur.close()
conn.close()
print(f"Executed {len(statements)} statements from {SCHEMA_PATH.name}")
