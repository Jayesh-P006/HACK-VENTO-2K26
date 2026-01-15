# Registration Troubleshooting Guide

## 🔴 Problem: Registration Button Not Working (No Message, No Animation, Nothing)

This guide will help you identify and fix the registration issue.

### Step 1: Check the Backend Server Status

**Is the Flask backend running?**

Open PowerShell and run:
```powershell
cd "f:\2. HACKVENTO 2K26\backend"
python start_server.py
```

You should see output like:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

If this fails, check if your database is configured:
1. Create `.env` file in the backend folder with:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=hackvento
DB_PORT=3306
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=jwt-secret-key
```

### Step 2: Check the Frontend Connection

1. Open the browser **Developer Tools** (Press F12)
2. Go to the **Console** tab
3. Refresh the register page
4. Look for any error messages starting with `[REGISTER]`

### Common Error Messages and Fixes:

#### Error: "Failed to load batches"
- **Cause**: Backend `/api/batches/active` endpoint not responding
- **Fix**: Make sure Flask backend is running (Step 1)

#### Error: "Cannot POST /api/auth/register"
- **Cause**: Endpoint not found or server crashed
- **Fix**: 
  1. Check Flask server console for error messages
  2. Restart Flask with: `python start_server.py`
  3. Make sure no other service is using port 5000

#### Error: "Failed to parse response JSON"
- **Cause**: Server returned HTML error page instead of JSON
- **Fix**: 
  1. Check Flask console for detailed error
  2. Look at the "Network" tab in Developer Tools
  3. Click on the failed request and check the "Response" tab

### Step 3: Manual Testing via Browser Console

If the form isn't working, test the API directly in the browser console:

```javascript
// Test 1: Check API connectivity
fetch('http://localhost:5000/api/batches/active')
  .then(r => r.json())
  .then(data => console.log('Batches:', data))
  .catch(e => console.error('Error:', e));

// Test 2: Try registering manually
fetch('http://localhost:5000/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'test.manual@example.com',
    password: 'password123',
    role_id: 1,
    full_name: 'Test Student',
    enrollment_number: 'EN2026001',
    branch: 'CSE',
    cgpa: 8.5,
    graduation_year: 2026,
    current_year: 3,
    batch_id: 1,
    phone: '9876543210'
  })
})
  .then(r => r.json())
  .then(data => console.log('Response:', data))
  .catch(e => console.error('Error:', e));
```

### Step 4: Check Database

Verify the database is properly set up:

```bash
cd "f:\2. HACKVENTO 2K26\backend"
python
```

Then in Python shell:
```python
from app import app, db
from models import User, Student, Batch, Department

with app.app_context():
    # Check if tables exist
    print(f"Users: {User.query.count()}")
    print(f"Students: {Student.query.count()}")
    print(f"Departments: {Department.query.count()}")
    print(f"Batches: {Batch.query.count()}")
    
    # Check if demo data exists
    batches = Batch.query.all()
    print(f"\nAvailable batches:")
    for b in batches:
        print(f"  - {b.batch_code} (ID: {b.id})")
```

### Step 5: Enable Debug Logging

The registration form now includes detailed console logging. Check the **Console** tab for messages starting with `[REGISTER]`:

```
[REGISTER] Page loaded. API_BASE: http://localhost:5000/api
[REGISTER] Form element: <form id="register-form">
[REGISTER] Submit button: <button id="register-submit">
[REGISTER] Loading batches from: http://localhost:5000/api/batches/active
[REGISTER] Batch response status: 200
[REGISTER] Batches loaded: [...]
```

### Step 6: Test with Test Script

Run the automated test:

```powershell
cd "f:\2. HACKVENTO 2K26\backend"
python test_registration.py
```

Expected output:
```
============================================================
TEST 0: Connection Check
============================================================
✓ API Server is reachable at http://localhost:5000

============================================================
TEST 1: Student Registration
============================================================
✓ Student registration test PASSED

✓ Admin registration test PASSED
...
```

### Step 7: Check for CORS Issues

If you see "CORS policy" errors in the console:

1. The backend has CORS enabled for `/api/*` routes
2. Check that the frontend is accessing `http://localhost:5000/api` (not https)
3. For production (Vercel), it should use `https://hack-vento-2k26-production.up.railway.app/api`

### Step 8: Clear Browser Cache

Sometimes stale JavaScript can cause issues:

1. Open DevTools (F12)
2. Right-click the refresh button → "Empty cache and hard refresh"
3. Or use: **Ctrl + Shift + Delete** → Clear cache → Refresh

---

## 🔧 Backend Debugging

If the frontend console shows errors, check the **Flask server console** for `[REGISTER]` logs:

```
[REGISTER] ========== NEW REGISTRATION REQUEST ==========
[REGISTER] Request method: POST
[REGISTER] Content-Type: application/json
[REGISTER] Received data keys: ['email', 'password', 'role_id', 'full_name', ...]
[REGISTER] Email: test@example.com
[REGISTER] Role ID: 1
[REGISTER] User created with ID: 42, Role: 1
[REGISTER] Creating Student profile...
[REGISTER] Student created with ID: 15
[REGISTER] StudentVerification created: 15
[REGISTER] SUCCESS: User test@example.com registered successfully
```

If you see errors like:
```
[REGISTER] EXCEPTION OCCURRED
[REGISTER] Exception type: IntegrityError
[REGISTER] Exception message: duplicate entry for email
```

This tells you exactly what went wrong.

---

## 📋 Quick Checklist

- [ ] Flask backend running on http://localhost:5000
- [ ] `.env` file configured with database credentials
- [ ] Database (MySQL) is running and accessible
- [ ] Browser console shows no `[REGISTER]` errors
- [ ] Batches are loading in the dropdown
- [ ] Form validates without errors
- [ ] After submit, check for `[REGISTER] SUCCESS` message

## 💡 Still Not Working?

1. **Check Flask server console** - The actual error will be there
2. **Check Browser DevTools Console** - Look for `[REGISTER]` logs
3. **Run test_registration.py** - This tests the API directly
4. **Share the error message** - Exact error helps debugging faster
