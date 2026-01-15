"""
Create admin-related tables for admin account management
This script creates:
- admins table
- admin_verification table
- admin_access_log table
"""

import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

# Connect to database
conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "placement_portal"),
    autocommit=True
)

cursor = conn.cursor()

# Create admins table
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

# Create admin_verification table
create_admin_verification_sql = """
CREATE TABLE IF NOT EXISTS admin_verification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL UNIQUE,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    verification_date TIMESTAMP NULL,
    approved_by INT,
    rejection_reason TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
);
"""

# Create admin_access_log table
create_admin_access_log_sql = """
CREATE TABLE IF NOT EXISTS admin_access_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    status VARCHAR(50),
    details TEXT,
    performed_by INT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE,
    FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL
);
"""

try:
    print("Creating admins table...")
    cursor.execute(create_admins_sql)
    print("✓ admins table created")
    
    print("Creating admin_verification table...")
    cursor.execute(create_admin_verification_sql)
    print("✓ admin_verification table created")
    
    print("Creating admin_access_log table...")
    cursor.execute(create_admin_access_log_sql)
    print("✓ admin_access_log table created")
    
    print("\n✓ All admin tables created successfully!")
except Exception as e:
    print(f"✗ Error: {e}")
finally:
    cursor.close()
    conn.close()
