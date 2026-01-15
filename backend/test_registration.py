#!/usr/bin/env python
"""Test script to verify registration endpoint is working"""

import sys
import requests
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Test configuration
BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api'

def test_student_registration():
    """Test student registration"""
    print('\n' + '='*60)
    print('TEST 1: Student Registration')
    print('='*60)
    
    payload = {
        'email': f'test.student.{int(__import__("time").time())}@example.com',
        'password': 'password123',
        'role_id': 1,
        'full_name': 'Test Student',
        'enrollment_number': 'EN2026001',
        'branch': 'CSE',
        'cgpa': 8.5,
        'graduation_year': 2026,
        'current_year': 3,
        'batch_id': 1,
        'phone': '9876543210'
    }
    
    print(f'Payload:\n{json.dumps(payload, indent=2)}')
    
    try:
        response = requests.post(f'{API_BASE}/auth/register', json=payload)
        print(f'\nResponse Status: {response.status_code}')
        print(f'Response Body:\n{json.dumps(response.json(), indent=2)}')
        
        if response.status_code == 201:
            print('✓ Student registration test PASSED')
            return True
        else:
            print('✗ Student registration test FAILED')
            return False
    except Exception as e:
        print(f'✗ Error: {str(e)}')
        return False

def test_company_registration():
    """Test company registration"""
    print('\n' + '='*60)
    print('TEST 2: Company Registration')
    print('='*60)
    
    payload = {
        'email': f'test.company.{int(__import__("time").time())}@example.com',
        'password': 'password123',
        'role_id': 2,
        'company_name': 'Test Tech Corp',
        'industry': 'Technology',
        'hr_name': 'HR Manager',
        'hr_phone': '8888888888'
    }
    
    print(f'Payload:\n{json.dumps(payload, indent=2)}')
    
    try:
        response = requests.post(f'{API_BASE}/auth/register', json=payload)
        print(f'\nResponse Status: {response.status_code}')
        print(f'Response Body:\n{json.dumps(response.json(), indent=2)}')
        
        if response.status_code == 201:
            print('✓ Company registration test PASSED')
            return True
        else:
            print('✗ Company registration test FAILED')
            return False
    except Exception as e:
        print(f'✗ Error: {str(e)}')
        return False

def test_admin_registration():
    """Test admin registration"""
    print('\n' + '='*60)
    print('TEST 3: Admin Registration')
    print('='*60)
    
    payload = {
        'email': f'test.admin.{int(__import__("time").time())}@example.com',
        'password': 'password123',
        'role_id': 3,
        'full_name': 'Test Admin',
        'phone': '7777777777',
        'department': 'Placement Cell',
        'verification_key': ''
    }
    
    print(f'Payload:\n{json.dumps(payload, indent=2)}')
    
    try:
        response = requests.post(f'{API_BASE}/auth/register', json=payload)
        print(f'\nResponse Status: {response.status_code}')
        print(f'Response Body:\n{json.dumps(response.json(), indent=2)}')
        
        if response.status_code == 201:
            print('✓ Admin registration test PASSED')
            return True
        else:
            print('✗ Admin registration test FAILED')
            return False
    except Exception as e:
        print(f'✗ Error: {str(e)}')
        return False

def test_connection():
    """Test if API is reachable"""
    print('\n' + '='*60)
    print('TEST 0: Connection Check')
    print('='*60)
    
    try:
        response = requests.get(f'{BASE_URL}/', timeout=5)
        print(f'✓ API Server is reachable at {BASE_URL}')
        return True
    except requests.exceptions.ConnectionError:
        print(f'✗ Cannot connect to {BASE_URL}')
        print('Make sure the Flask backend is running with: python start_server.py')
        return False
    except Exception as e:
        print(f'✗ Connection error: {str(e)}')
        return False

if __name__ == '__main__':
    print('\n🔍 Registration Endpoint Test Suite')
    
    # Test connection first
    if not test_connection():
        sys.exit(1)
    
    # Run tests
    results = {
        'Student Registration': test_student_registration(),
        'Company Registration': test_company_registration(),
        'Admin Registration': test_admin_registration(),
    }
    
    # Summary
    print('\n' + '='*60)
    print('TEST SUMMARY')
    print('='*60)
    for test_name, passed in results.items():
        status = '✓ PASSED' if passed else '✗ FAILED'
        print(f'{test_name}: {status}')
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f'\nTotal: {passed}/{total} tests passed')
    
    if passed == total:
        print('\n🎉 All tests passed!')
        sys.exit(0)
    else:
        print(f'\n⚠️  {total - passed} test(s) failed')
        sys.exit(1)
