#!/usr/bin/env python3
"""Test if the backend can start without errors"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

print("Testing backend startup...")
print("=" * 50)

try:
    print("[1/4] Importing Flask...")
    from flask import Flask
    print("✅ Flask imported")
    
    print("[2/4] Importing models...")
    from models import db, Department, Batch
    print("✅ Models imported")
    
    print("[3/4] Importing app...")
    from app import app
    print("✅ App imported")
    
    print("[4/4] Checking routes...")
    with app.app_context():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f"{rule.methods} {rule.rule}")
        
        print(f"✅ Found {len(routes)} routes")
        print("\nKey routes:")
        for route in sorted(routes):
            if '/api/health' in route or '/batches/active' in route or '/auth/register' in route:
                print(f"  - {route}")
    
    print("\n" + "=" * 50)
    print("✅ Backend startup test PASSED")
    print("\nBackend should start successfully on Railway!")
    sys.exit(0)
    
except Exception as e:
    print("\n" + "=" * 50)
    print("❌ Backend startup test FAILED")
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
