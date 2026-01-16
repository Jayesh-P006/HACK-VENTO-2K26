"""Clear all students except demo account"""
import os
import pymysql

# Connect to Railway MySQL database
conn = pymysql.connect(
    host=os.getenv('MYSQLHOST'),
    user=os.getenv('MYSQLUSER'),
    password=os.getenv('MYSQLPASSWORD'),
    database=os.getenv('MYSQLDATABASE'),
    port=int(os.getenv('MYSQLPORT', 3306))
)

cur = conn.cursor()

print('Connected to database!')

# Count current students
cur.execute('SELECT COUNT(*) FROM students')
before_count = cur.fetchone()[0]
print(f'Students before cleanup: {before_count}')

# Step 1: Delete verification records for non-demo students
print('Deleting student_verification records...')
cur.execute('''
    DELETE FROM student_verification 
    WHERE student_id IN (
        SELECT id FROM students WHERE enrollment_number != 'DEMO2026001'
    )
''')
print(f'  Deleted {cur.rowcount} verification records')

# Step 2: Get user_ids before deleting students
cur.execute('SELECT user_id FROM students WHERE enrollment_number != "DEMO2026001"')
user_ids_to_delete = [row[0] for row in cur.fetchall()]
print(f'  Found {len(user_ids_to_delete)} user accounts to delete')

# Step 3: Delete non-demo students
print('Deleting students...')
cur.execute('DELETE FROM students WHERE enrollment_number != "DEMO2026001"')
deleted_students = cur.rowcount
print(f'  Deleted {deleted_students} students')

# Step 4: Delete associated user accounts
if user_ids_to_delete:
    print('Deleting user accounts...')
    placeholders = ','.join(['%s'] * len(user_ids_to_delete))
    cur.execute(f'DELETE FROM users WHERE id IN ({placeholders}) AND role_id = 1', user_ids_to_delete)
    print(f'  Deleted {cur.rowcount} user accounts')

# Commit changes
conn.commit()

# Verify
cur.execute('SELECT COUNT(*) FROM students')
after_count = cur.fetchone()[0]
print(f'\nStudents after cleanup: {after_count}')

cur.execute('SELECT id, full_name, enrollment_number, branch FROM students')
for student in cur.fetchall():
    print(f'  - {student[1]} ({student[2]}) - {student[3]}')

cur.close()
conn.close()

print('\n✅ Cleanup completed successfully!')
