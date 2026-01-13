#!/usr/bin/env python3
"""
Reset and initialize the database
"""
import pymysql
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'placement_portal')

try:
    print("Connecting to MySQL...")
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    # Drop and recreate database
    print(f"Dropping database {DB_NAME}...")
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    print(f"Creating database {DB_NAME}...")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    
    cursor.close()
    conn.close()
    
    # Connect to the new database
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    # Read and execute schema
    schema_file = Path(__file__).parent / "database" / "schema.sql"
    print(f"Reading schema from {schema_file}...")
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Execute statements
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    for i, stmt in enumerate(statements):
        if stmt and not stmt.startswith('--'):
            try:
                cursor.execute(stmt)
                print(f"✓ Statement {i+1}/{len(statements)}")
            except Exception as e:
                print(f"Error in statement {i+1}: {str(e)[:100]}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Database initialized successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
