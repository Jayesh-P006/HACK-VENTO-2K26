#!/usr/bin/env python3
"""
Diagnostic script to check batches table status
Run with: railway run python backend/diagnose_batches.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment variables from the backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Build connection string
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', 3306)
db_name = os.getenv('DB_NAME')

connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

print(f"[DIAGNOSE] Connecting to: {db_host}:{db_port}/{db_name}")

try:
    engine = create_engine(connection_string)
    
    # Test connection
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("[DIAGNOSE] ✓ Database connection successful")
    
    # Check tables
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    print(f"\n[DIAGNOSE] Tables found: {len(all_tables)}")
    for table in sorted(all_tables):
        print(f"  - {table}")
    
    # Check batches table
    has_batches = 'batches' in all_tables
    print(f"\n[DIAGNOSE] batches table exists: {has_batches}")
    
    if has_batches:
        # Count batches
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) as cnt FROM batches"))
            count = result.fetchone()[0]
            print(f"[DIAGNOSE] batches row count: {count}")
            
            # Show batches
            result = connection.execute(text("SELECT id, batch_code, status FROM batches"))
            rows = result.fetchall()
            print(f"[DIAGNOSE] batches content:")
            for row in rows:
                print(f"  - ID: {row[0]}, Code: {row[1]}, Status: {row[2]}")
    else:
        print("[DIAGNOSE] ✗ batches table NOT FOUND")
    
    # Check departments
    has_departments = 'departments' in all_tables
    print(f"\n[DIAGNOSE] departments table exists: {has_departments}")
    
    if has_departments:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT COUNT(*) as cnt FROM departments"))
            count = result.fetchone()[0]
            print(f"[DIAGNOSE] departments row count: {count}")

except Exception as e:
    print(f"[DIAGNOSE] ✗ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
