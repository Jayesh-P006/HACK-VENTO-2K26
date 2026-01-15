# ✅ Registration System - Verification Checklist

## Before You Start

Make sure you have:
- ✅ Python 3.8+ installed
- ✅ MySQL running and accessible
- ✅ `.env` file in `f:\2. HACKVENTO 2K26\backend\` with database credentials
- ✅ Node.js/Bun installed for frontend
- ✅ Bun lockfile (`frontend/bun.lockb`) or npm packages installed

---

## Phase 1: Backend Setup (Terminal 1)

### Step 1: Navigate to Backend
```powershell
cd "f:\2. HACKVENTO 2K26\backend"
```

### Step 2: Check .env File
Verify this file exists with your database credentials:
```
File: f:\2. HACKVENTO 2K26\backend\.env
Content:
  DB_HOST=localhost
  DB_USER=root
  DB_PASSWORD=your_password
  DB_NAME=hackvento
  DB_PORT=3306
```

### Step 3: Start Flask Server
```powershell
python start_server.py
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
[db] initializing database...
[db] Creating demo accounts...
[db] Seeding master data...
[db] fix demo accounts...
```

### ✓ Verification
- [ ] Server is running on http://127.0.0.1:5000
- [ ] No error messages in console
- [ ] See "Seeding master data..." log
- [ ] Console shows database initialization success

---

## Phase 2: Frontend Setup (Terminal 2)

### Step 1: Open New Terminal

### Step 2: Navigate to Frontend
```powershell
cd "f:\2. HACKVENTO 2K26\frontend"
```

### Step 3: Check Dependencies
```powershell
bun install
```
Or:
```powershell
npm install
```

### Step 4: Start Dev Server
```powershell
bun run dev
```
Or:
```powershell
npm run dev
```

**Expected Output:**
```
  VITE v... ready in ... ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

### ✓ Verification
- [ ] Frontend is running on http://localhost:5173/
- [ ] No TypeScript errors
- [ ] Server is ready

---

## Phase 3: Test Registration (Browser)

### Step 1: Open Registration Form
Navigate to:
```
http://localhost:5173/public/portal/register.html
```

### Step 2: Open DevTools Console
Press **F12** on your keyboard, then click **Console** tab

### Step 3: Register as Student

**Form Fields:**
| Field | Value |
|-------|-------|
| Role | 🎓 Student |
| Email | `teststudent001@example.com` |
| Password | `password123` |
| Confirm Password | `password123` |
| Full Name | `Test Student` |
| Enrollment Number | `EN2026001` |
| Branch | `CSE` |
| CGPA | `8.5` |
| Current Year | `3` |
| Batch | `2023-27 (BTech - Engineering)` |
| Phone | `9876543210` |

### Step 4: Click "Create Account"

### Step 5: Check Console Logs

You should see in the **Console** tab:
```
[REGISTER] Page loaded. API_BASE: http://localhost:5000/api
[REGISTER] Form submit event triggered
[REGISTER] Current role: 1
[REGISTER] Sending registration payload: {...}
[REGISTER] Response status: 201
[REGISTER] Registration response: {message: "Registration successful...", user: {...}}
```

### Step 6: Check Flask Console

In Terminal 1 (Flask server), you should see:
```
[REGISTER] ========== NEW REGISTRATION REQUEST ==========
[REGISTER] Request method: POST
[REGISTER] Content-Type: application/json
[REGISTER] Email: teststudent001@example.com
[REGISTER] Role ID: 1
[REGISTER] User created with ID: X, Role: 1
[REGISTER] Creating Student profile...
[REGISTER] Student created with ID: Y
[REGISTER] StudentVerification created: Y
[REGISTER] SUCCESS: User teststudent001@example.com registered successfully
```

### ✓ Verification
- [ ] Form submits (button text changes to "Creating account...")
- [ ] Success message appears (green toast: "Account created successfully!")
- [ ] Redirected to login page after 1.5 seconds
- [ ] Browser console shows all `[REGISTER]` logs
- [ ] Flask console shows success message

---

## Phase 4: Test Login (Browser)

### Step 1: You Should Be On Login Page
```
http://localhost:5173/public/portal/index.html
```

### Step 2: Login with Registered Email
| Field | Value |
|-------|-------|
| Email | `teststudent001@example.com` |
| Password | `password123` |

### Step 3: Click "Sign in"

### Step 4: Expected Result
You should see:
```
⏳ Account not verified by admin

Your account is pending verification from the admin. 
Please wait for the admin to review and approve your account.
```

### ✓ Verification
- [ ] Login attempt accepted
- [ ] Verification pending message appears
- [ ] No error messages

---

## Phase 5: Test Admin Verification (Optional)

### Step 1: Open Admin Dashboard
```
http://localhost:5173/public/portal/admin-dashboard.html
```

### Step 2: Login as Admin
```
Email: admin@university.edu
Password: admin123
```

### Step 3: Check Verification Queue
1. Go to **Verification Queue** tab
2. You should see your newly registered student
3. Click **Approve** button

### Step 4: Back to Student Login
Now try logging in again as your student account - it should work!

### ✓ Verification
- [ ] Student appears in admin verification queue
- [ ] Approve button works
- [ ] Student can now login after approval

---

## Phase 6: Run Automated Tests (Terminal 3)

### Step 1: Open New Terminal

### Step 2: Navigate to Backend
```powershell
cd "f:\2. HACKVENTO 2K26\backend"
```

### Step 3: Run Test Suite
```powershell
python test_registration.py
```

### Step 4: Check Results
You should see:
```
============================================================
TEST 0: Connection Check
============================================================
✓ API Server is reachable at http://localhost:5000

============================================================
TEST 1: Student Registration
============================================================
✓ Student registration test PASSED

============================================================
TEST 2: Company Registration
============================================================
✓ Company registration test PASSED

============================================================
TEST 3: Admin Registration
============================================================
✓ Admin registration test PASSED

============================================================
TEST SUMMARY
============================================================
Student Registration: ✓ PASSED
Company Registration: ✓ PASSED
Admin Registration: ✓ PASSED

Total: 3/3 tests passed

🎉 All tests passed!
```

### ✓ Verification
- [ ] All 3 tests pass (Student, Company, Admin)
- [ ] No connection errors
- [ ] Response status codes are 201 (Created)

---

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Form doesn't respond when clicked | Flask backend not running | Start with `python start_server.py` |
| No logs in browser console | Frontend not connected to backend | Check API_BASE URL, check CORS |
| Batch dropdown is empty | `/api/batches/active` not working | Check Flask console for errors |
| "Email already exists" error | Using same email twice | Use different email address |
| "Database error" in Flask console | MySQL not running or wrong credentials | Check `.env` file, verify MySQL |
| "Cannot connect to server" | Wrong API URL | Check it's http://localhost:5000 (not https) |
| Form validation errors | Missing required fields | Fill all fields including phone |
| Nothing happens on submit | Check browser F12 console | Look for `[REGISTER]` error logs |

---

## Database Verification

To check if everything was created correctly:

```powershell
cd "f:\2. HACKVENTO 2K26\backend"
python
```

Then in Python shell:
```python
from app import app, db
from models import User, Student, Batch, Department

with app.app_context():
    print(f"Users: {User.query.count()}")
    print(f"Students: {Student.query.count()}")
    print(f"Departments: {Department.query.count()}")
    print(f"Batches: {Batch.query.count()}")
    
    # List all batches
    for batch in Batch.query.all():
        print(f"  - {batch.batch_code} (ID: {batch.id}, Active: {batch.is_active})")
```

---

## Key Files Involved

| File | Purpose | Status |
|------|---------|--------|
| `frontend/public/portal/register.html` | Registration form with enhanced logging | ✅ Updated |
| `backend/app.py` | Registration endpoint with debug logs | ✅ Updated |
| `backend/start_server.py` | Flask startup script | ✅ Working |
| `backend/models.py` | Database models | ✅ Complete |
| `backend/test_registration.py` | Automated test script | ✅ New |
| `.env` | Database configuration | ⏳ User must create |

---

## Success Indicators

✅ **All systems working when you see:**

1. **Backend Console:**
   ```
   [db] Seeding master data...
   [db] Departments created/already exist
   [db] Batches created/already exist
   ```

2. **Frontend:**
   - Batch dropdown populated with options
   - Form validates inputs
   - Error messages appear when needed

3. **Registration Process:**
   - Form submits successfully
   - Console shows `[REGISTER]` logs
   - Redirect to login after success
   - Can see pending verification message

4. **Admin Approval:**
   - Student appears in admin verification queue
   - Admin can approve/reject
   - Student can login after approval

---

## 🎉 You're All Set!

If you've completed all phases and verified all checkpoints, your registration system is fully functional and debuggable!

**Need Help?**
- See `REGISTRATION_TROUBLESHOOTING.md` for detailed diagnostics
- See `QUICK_START.md` for quick reference
- See `REGISTRATION_FIX_SUMMARY.md` for what was fixed
- Run `python test_registration.py` for automated testing
