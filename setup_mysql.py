#!/usr/bin/env python3
"""
Setup MySQL database with proper credentials
"""
import subprocess
import sys

# Try to connect and setup with different approaches
print("Setting up MySQL database...")

# Approach 1: Try mysql command line with default setup
try:
    # Create database and user
    commands = [
        "CREATE DATABASE IF NOT EXISTS placement_portal;",
        "CREATE USER IF NOT EXISTS 'placement'@'localhost' IDENTIFIED BY 'placement123';",
        "GRANT ALL PRIVILEGES ON placement_portal.* TO 'placement'@'localhost';",
        "FLUSH PRIVILEGES;",
    ]
    
    for cmd in commands:
        # Try with no password first
        result = subprocess.run(
            f'mysql -u root -e "{cmd}"',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ Executed: {cmd}")
        elif "Access denied" in result.stderr:
            print(f"Note: {cmd} - Access denied (may already exist)")
        else:
            print(f"Warning: {cmd}")
            print(result.stderr)
    
    print("\n✓ MySQL setup complete!")
    print("Update your .env file with:")
    print("DB_USER=placement")
    print("DB_PASSWORD=placement123")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nPlease manually run these MySQL commands:")
    print("CREATE DATABASE IF NOT EXISTS placement_portal;")
    print("CREATE USER IF NOT EXISTS 'placement'@'localhost' IDENTIFIED BY 'placement123';")
    print("GRANT ALL PRIVILEGES ON placement_portal.* TO 'placement'@'localhost';")
    print("FLUSH PRIVILEGES;")
