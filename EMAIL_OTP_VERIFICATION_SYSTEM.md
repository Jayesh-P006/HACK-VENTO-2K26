# EMAIL-OTP Verification System Implementation

## 🎯 Overview

A complete EMAIL-OTP verification system has been implemented for the Silent Syntax Portal. Users now must verify their email via OTP before they can access the portal.

### Flow:
1. **User Registers** → Backend generates OTP and sends via email
2. **Redirect to OTP Page** → User enters 6-digit code from email
3. **Verify OTP** → Code is validated (10-minute expiry)
4. **Success Message** → "Email verified. Pending admin approval"
5. **Admin Approves** → User gets access to portal

---

## 📋 System Components

### 1. Backend Changes

#### A. Database Models Updated
**File:** `backend/models.py`

Added to `StudentVerification` and `AdminVerification` models:
```python
otp = db.Column(db.String(6))  # 6-digit OTP
otp_verified = db.Column(db.Boolean, default=False)  # Has email been verified?
otp_sent_at = db.Column(db.DateTime)  # When OTP was sent
otp_verified_at = db.Column(db.DateTime)  # When OTP was verified
otp_attempts = db.Column(db.Integer, default=0)  # Failed OTP attempts
```

#### B. OTP Service Module
**File:** `backend/otp_service.py` (NEW)

Functions provided:
- `generate_otp(length=6)` - Creates random 6-digit code
- `send_otp_email(email, full_name, otp)` - Sends HTML email with OTP
- `is_otp_valid(otp_record)` - Checks if OTP is still valid (10-min window)
- `send_approval_pending_email(email, full_name, role_type)` - Notifies user of pending approval

#### C. New API Endpoints
**File:** `backend/app.py`

**Endpoint 1: Send OTP**
```
POST /api/auth/send-otp
Body: { "email": "user@example.com" }
Response: { "success": true, "message": "OTP sent to..." }
```

**Endpoint 2: Verify OTP**
```
POST /api/auth/verify-otp
Body: { "email": "user@example.com", "otp": "123456" }
Response: { "success": true, "email_verified": true, "next_step": "await_admin_approval" }
```

**Updated Endpoint: Register**
```
POST /api/auth/register
Response now includes: { "next_step": "otp_verification", "email": "...", "role_type": "student" }
```

#### D. Email Templates
Professional HTML emails for:
- OTP verification code (with 10-min countdown)
- Approval pending notification (after OTP verified)

---

### 2. Frontend Changes

#### A. OTP Verification Page
**File:** `frontend/public/portal/verify-email-otp.html` (NEW)

Features:
- 6-digit code input with auto-focus/navigation
- 10-minute countdown timer
- Paste support (paste full code at once)
- "Resend Code" button with cooldown
- Approval message on success
- Error messages with attempt counter
- Responsive design matching portal theme

**Key Interactions:**
- Input boxes auto-advance to next when digit entered
- Backspace auto-goes to previous box
- Paste support for pasting entire code
- Real-time timer display
- Smart error messages

#### B. Updated Registration Page
**File:** `frontend/public/portal/register.html`

Modified to:
- Redirect to OTP verification page after successful registration
- Pass email and role type as URL parameters
- Show success toast before redirect

**New Flow:**
```javascript
// Before: window.location.href = 'index.html'
// After: window.location.href = 'verify-email-otp.html?email=user@example.com&role=student'
```

---

## 🔒 Security Features

1. **OTP Validity**
   - Valid for 10 minutes only
   - Expires automatically
   - Must be regenerated if expired

2. **Attempt Limiting**
   - Maximum 5 failed attempts
   - Locked after 5 attempts
   - Requires new OTP request

3. **OTP Format**
   - 6 random digits
   - No sequential numbers
   - Unique per registration

4. **Email Verification**
   - Required before portal access
   - Separate from admin approval
   - User notified at each step

---

## 🚀 Testing the System

### Step 1: Start Backend
```powershell
cd "f:\2. HACKVENTO 2K26\backend"
python start_server.py
```

### Step 2: Start Frontend
```powershell
cd "f:\2. HACKVENTO 2K26\frontend"
npm run dev
```

### Step 3: Test Registration Flow

#### Test Case 1: Student Registration
1. Go to: `http://localhost:5173/public/portal/register.html`
2. Fill form:
   - Email: `teststudent@example.com`
   - Password: `password123`
   - All required student fields
3. Click "Create Account"
4. Should see: "Account created! Check your email for verification code..."
5. Redirected to OTP page

#### Test Case 2: Verify OTP
1. On OTP page, you'll see email: `teststudent@example.com`
2. Check **console logs** for OTP (backend prints it)
   - Look for: `[OTP] Email sent to teststudent@example.com with OTP: 123456`
3. Enter 6-digit code
4. Click "Verify Email"
5. Should see success: "Email verified successfully!"
6. Approval message displayed

#### Test Case 3: Resend OTP
1. Click "Send code again"
2. New OTP generated and sent
3. Timer restarts (10 minutes)
4. Can enter new code

#### Test Case 4: Invalid OTP
1. Enter wrong code (e.g., 000000)
2. Should see: "Incorrect code. 5 attempts remaining"
3. After 5 attempts: "Too many failed attempts"

#### Test Case 5: Expired OTP
1. Wait 10 minutes or manually expire OTP
2. Should see: "OTP has expired"
3. Must click "Send code again"

---

## 📧 Email Configuration

For OTP emails to send, configure in `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@hackvento.com
```

**For Testing Without Email:**
- Backend prints OTP to console
- Check server output for: `[OTP] Email sent to ... with OTP: 123456`

---

## 🔍 Console Logging

Both backend and frontend provide detailed logging with `[OTP]` prefix:

**Frontend Console:**
```
[OTP] Email from URL: teststudent@example.com
[OTP] Role type: student
[OTP] 🔥 Form submitted!
[OTP] Verifying OTP: 123456
[OTP] ✅ Email verified successfully!
```

**Backend Console:**
```
[OTP] ========== SEND OTP REQUEST ==========
[OTP] Email: teststudent@example.com
[OTP] OTP generated: 123456
[OTP] Email sent to teststudent@example.com with OTP: 123456

[OTP] ========== VERIFY OTP REQUEST ==========
[OTP] Email: teststudent@example.com
[OTP] OTP submitted: 123456
[OTP] OTP verified successfully for teststudent@example.com
```

---

## 📊 Database Schema Changes

### StudentVerification Table
```
id (PK)
student_id (FK) 
status (Pending/Verified/Rejected)
otp (varchar 6) ← NEW
otp_verified (boolean) ← NEW
otp_sent_at (datetime) ← NEW
otp_verified_at (datetime) ← NEW
otp_attempts (int) ← NEW
... existing fields ...
```

### AdminVerification Table
```
id (PK)
admin_id (FK)
status (Pending/Approved/Rejected)
otp (varchar 6) ← NEW
otp_verified (boolean) ← NEW
otp_sent_at (datetime) ← NEW
otp_verified_at (datetime) ← NEW
otp_attempts (int) ← NEW
... existing fields ...
```

---

## 🔄 API Response Examples

### Register Response (Success)
```json
{
  "message": "Registration successful! OTP sent to teststudent@example.com. Please verify your email.",
  "user": {
    "id": 42,
    "email": "teststudent@example.com",
    "role_id": 1,
    "is_verified": false,
    "created_at": "2026-01-15T10:30:00"
  },
  "role_type": "student",
  "email": "teststudent@example.com",
  "next_step": "otp_verification"
}
```

### Send OTP Response (Success)
```json
{
  "success": true,
  "message": "OTP sent to teststudent@example.com",
  "email": "teststudent@example.com",
  "otp_length": 6
}
```

### Verify OTP Response (Success)
```json
{
  "success": true,
  "message": "Email verified successfully!",
  "email_verified": true,
  "user": {...},
  "next_step": "await_admin_approval"
}
```

### Verify OTP Response (Invalid)
```json
{
  "error": "Invalid OTP",
  "message": "Incorrect verification code. 4 attempts remaining.",
  "attempts_remaining": 4
}
```

### Verify OTP Response (Expired)
```json
{
  "error": "OTP has expired",
  "message": "Your verification code has expired. Please request a new one.",
  "expired": true
}
```

---

## 🎯 User Journey Map

```
┌─────────────┐
│  Register   │
│ (Fill Form) │
└──────┬──────┘
       │ POST /api/auth/register
       ↓
┌──────────────────────────┐
│ User Created + OTP Gen   │
│ Email Sent with OTP      │
│ Response: next_step=otp  │
└──────┬───────────────────┘
       │ Redirect to verify-email-otp.html?email=...&role=...
       ↓
┌──────────────────────────┐
│ OTP Verification Page    │
│ - Input 6 digits         │
│ - 10-min timer           │
│ - Resend option          │
└──────┬───────────────────┘
       │ POST /api/auth/verify-otp
       ↓
     SUCCESS?
       │
     YES↓ NO
       │  └─→ "Invalid/Expired OTP" → Retry
       │
┌──────────────────────────┐
│ ✅ Email Verified        │
│ Approval Message Shows   │
│ - Wait for admin         │
│ - 24hr approval window   │
└──────┬───────────────────┘
       │ User clicks "Go to Login"
       ↓
┌──────────────────────────┐
│ Login Page               │
│ - Cannot login yet       │
│ - Awaiting admin approval│
└──────────────────────────┘
       
       (Simultaneously)
       ↓
┌──────────────────────────┐
│ Admin Dashboard          │
│ - Views pending users    │
│ - Approves account       │
│ - User notified by email │
└──────┬───────────────────┘
       │ Admin clicks Approve
       ↓
┌──────────────────────────┐
│ ✅ Account Approved      │
│ User can now login       │
│ Full portal access       │
└──────────────────────────┘
```

---

## 🧪 Troubleshooting

### Problem: No OTP email received
**Solution:** 
1. Check console logs for `[OTP] Email sent to ...`
2. Check MAIL_SERVER configuration in .env
3. Check spam folder
4. For testing: OTP is printed in server console

### Problem: OTP page shows blank
**Solution:**
1. Check URL has `?email=...&role=...` parameters
2. Check browser console for errors
3. Verify verify-email-otp.html exists

### Problem: "OTP expired" error
**Solution:**
1. OTP is valid for 10 minutes only
2. Click "Send code again" to get new OTP
3. Timer is shown on page (⏱️)

### Problem: "Too many attempts" error
**Solution:**
1. Maximum 5 failed attempts allowed
2. Click "Send code again" to reset
3. New OTP will be generated

---

## 📁 Files Modified/Created

### Created:
- `backend/otp_service.py` - OTP generation and email sending
- `frontend/public/portal/verify-email-otp.html` - OTP verification page

### Modified:
- `backend/models.py` - Added OTP fields to StudentVerification, AdminVerification
- `backend/app.py` - Added send-otp, verify-otp endpoints, updated register endpoint
- `frontend/public/portal/register.html` - Redirect to OTP page after registration

---

## ✅ Implementation Checklist

- [x] Database models updated with OTP fields
- [x] OTP generation function created
- [x] Email sending function created  
- [x] Send OTP endpoint (/api/auth/send-otp)
- [x] Verify OTP endpoint (/api/auth/verify-otp)
- [x] Register endpoint updated to send OTP
- [x] OTP verification page created (verify-email-otp.html)
- [x] Register page updated to redirect to OTP page
- [x] Approval pending email notification
- [x] 10-minute OTP validity window
- [x] OTP attempt limiting (5 max)
- [x] Resend OTP functionality
- [x] Console logging for debugging
- [x] Error handling and messages
- [x] Success message and approval info

---

## 🎓 Next Steps

1. **Configure Email** (Optional but recommended)
   - Set MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD in .env
   - Emails will be sent to users

2. **Test Complete Flow**
   - Register → OTP → Approval → Login
   - Verify all error scenarios

3. **Monitor Logs**
   - Check `[OTP]` logs in console
   - Debug any issues

4. **Deploy to Production**
   - Update production .env with email config
   - OTP will be sent to real email addresses
   - Users will see complete flow

---

**System Status:** ✅ READY FOR TESTING

All components implemented and integrated. Ready for production deployment.
