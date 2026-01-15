# 🚀 Quick Start Guide - Registration System

## Prerequisites
- Python 3.8+ installed
- MySQL database running
- Node.js/Bun installed (for frontend)
- `.env` file configured in backend folder

## 1️⃣ Configure Database (.env)

Create file: `f:\2. HACKVENTO 2K26\backend\.env`

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=hackvento
DB_PORT=3306
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production
ADMIN_CREATION_KEY=
MAIL_SERVER=
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@hackvento.com
```

## 2️⃣ Start Backend

```powershell
cd "f:\2. HACKVENTO 2K26\backend"
python start_server.py
```

**Expected output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
[db] initializing database...
[db] Creating demo accounts...
[db] Seeding master data...
[db] fix demo accounts...
```

## 3️⃣ Start Frontend

In a **new PowerShell window**:

```powershell
cd "f:\2. HACKVENTO 2K26\frontend"
npm run dev
```

Or with Bun:
```powershell
bun run dev
```

**Expected output:**
```
VITE v... ready in ... ms

➜  Local:   http://localhost:5173/
```

## 4️⃣ Register a Student Account

1. Open browser to: `http://localhost:5173/public/portal/register.html`
2. Select **🎓 Student** role
3. Fill in the form:
   - Email: `newstudent@example.com`
   - Password: `password123`
   - Full Name: `John Doe`
   - Enrollment: `EN2026001`
   - Branch: `CSE`
   - CGPA: `8.5`
   - Year: `3`
   - Batch: Select from dropdown (e.g., "2023-27")
   - Phone: `9876543210`
4. Click **Create Account**

## 5️⃣ Check Console for Logs

**Browser Console (F12):**
Look for `[REGISTER]` messages showing:
```
[REGISTER] Page loaded. API_BASE: http://localhost:5000/api
[REGISTER] Form submit event triggered
[REGISTER] Sending registration payload: {...}
[REGISTER] Response status: 201
[REGISTER] SUCCESS...
```

**Flask Server Console:**
Look for:
```
[REGISTER] ========== NEW REGISTRATION REQUEST ==========
[REGISTER] User created with ID: 42, Role: 1
[REGISTER] Student created with ID: 15
[REGISTER] SUCCESS: User newstudent@example.com registered successfully
```

## 6️⃣ Login and Verify

1. Go to: `http://localhost:5173/public/portal/index.html`
2. Login with the email you just registered
3. You should see a **verification pending** message

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot connect to backend" | Check Flask is running on http://localhost:5000 |
| "Failed to load batches" | Check Flask console - /api/batches/active endpoint error |
| "Email already exists" | Register with a different email address |
| "Database error" | Check MySQL is running, verify .env credentials |
| Nothing happens on submit | Check F12 console for `[REGISTER]` error messages |

## Database Tables Created

On first run, the system auto-creates:
- `users` - User accounts
- `students` - Student profiles
- `companies` - Company profiles
- `admins` - Admin accounts
- `student_verification` - Student approval queue
- `admin_verification` - Admin approval queue
- `batches` - Academic batches (auto-seeded)
- `departments` - Branches/departments (auto-seeded)

## Demo Accounts (Created Automatically)

```
Student:  student@university.edu / student123
Company:  company@tech.com / company123
Admin:    admin@university.edu / admin123
```

## File Locations

- Frontend: `f:\2. HACKVENTO 2K26\frontend\`
- Backend: `f:\2. HACKVENTO 2K26\backend\`
- Register Form: `f:\2. HACKVENTO 2K26\frontend\public\portal\register.html`
- Register Endpoint: `f:\2. HACKVENTO 2K26\backend\app.py` (line 303)
