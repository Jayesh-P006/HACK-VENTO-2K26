from werkzeug.security import generate_password_hash
import pymysql

# Generate hashes for demo accounts
hashes = {
    'admin@university.edu': generate_password_hash('admin123'),
    'student@university.edu': generate_password_hash('student123'),
    'company@tech.com': generate_password_hash('company123'),
}

print("Generated password hashes:")
for email, hash_val in hashes.items():
    print(f"{email}: {hash_val}")

# Connect and update
conn = pymysql.connect(host="localhost", user="root", password="jpassword", database="placement_portal", autocommit=True)
cur = conn.cursor()

for email, hash_val in hashes.items():
    cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hash_val, email))

cur.close()
conn.close()
print("\nUpdated database with correct password hashes")
