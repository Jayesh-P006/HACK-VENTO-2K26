import argparse
import os
import re
import sys
from urllib.parse import urlparse
from pathlib import Path


def _strip_sql_comments(sql: str) -> str:
    # Remove /* ... */ comments
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    # Remove -- ... comments
    sql = re.sub(r"^\s*--.*$", "", sql, flags=re.MULTILINE)
    return sql


def _split_statements(sql: str):
    """Split SQL into statements.

    This is intentionally simple: our schema file contains only DDL with ';' delimiters
    and no stored procedures/triggers.
    """
    cleaned = _strip_sql_comments(sql)
    parts = [p.strip() for p in cleaned.split(";")]
    return [p for p in parts if p]


def _get_env(name: str, fallbacks=()):
    v = os.getenv(name)
    if v:
        return v
    for fb in fallbacks:
        v = os.getenv(fb)
        if v:
            return v
    return None


def _parse_mysql_url(url: str):
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


def _db_config_from_env():
    # Prefer Railway's public proxy when available (works from local machines).
    mysql_public_url = _get_env("MYSQL_PUBLIC_URL")
    if mysql_public_url:
        try:
            return _parse_mysql_url(mysql_public_url)
        except Exception:
            # Fall back to discrete vars below.
            pass

    # Fallback to discrete vars.
    host = _get_env("MYSQLHOST", ("DB_HOST",))
    user = _get_env("MYSQLUSER", ("DB_USER",))
    password = _get_env("MYSQLPASSWORD", ("DB_PASSWORD",))
    database = _get_env("MYSQLDATABASE", ("DB_NAME",))
    port = _get_env("MYSQLPORT", ("DB_PORT",))

    # If Railway only provided an internal hostname, try the TCP proxy domain/port.
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
            "Missing required DB env vars: " + ", ".join(missing) +
            "\nTip: run via `railway run ...` so env vars are injected."
        )

    try:
        port_i = int(port) if port else 3306
    except ValueError:
        port_i = 3306

    return host, user, password or "", database, port_i


def main():
    parser = argparse.ArgumentParser(description="Run a .sql schema file against MySQL using env vars (Railway-friendly)")
    parser.add_argument("sql_file", type=str, help="Path to a .sql file")
    parser.add_argument("--dry-run", action="store_true", help="Print statements without executing")
    args = parser.parse_args()

    sql_path = Path(args.sql_file)
    if not sql_path.exists():
        raise SystemExit(f"SQL file not found: {sql_path}")

    sql = sql_path.read_text(encoding="utf-8")
    statements = _split_statements(sql)

    if args.dry_run:
        for i, st in enumerate(statements, start=1):
            print(f"\n--- Statement {i} ---\n{st}\n")
        print(f"\n(dry-run) Total statements: {len(statements)}")
        return

    try:
        import pymysql
    except Exception as e:
        raise SystemExit(
            "PyMySQL is not available in this environment. "
            "Install it with `python -m pip install PyMySQL` or install backend requirements.\n"
            f"Import error: {e}"
        )

    host, user, password, database, port = _db_config_from_env()

    print(f"Connecting to MySQL at {host}:{port}, db={database}...")
    conn = pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=port,
        autocommit=False,
        charset="utf8mb4",
    )

    try:
        with conn.cursor() as cur:
            for idx, st in enumerate(statements, start=1):
                cur.execute(st)
                if idx % 10 == 0:
                    conn.commit()
            conn.commit()
        print(f"✅ Applied schema successfully ({len(statements)} statements).")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
