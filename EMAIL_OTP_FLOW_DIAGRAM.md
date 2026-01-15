# EMAIL-OTP VERIFICATION - COMPLETE SYSTEM FLOW

## 🎯 Registration → Email Verification → Admin Approval → Portal Access

```
═══════════════════════════════════════════════════════════════════════════════
                           USER REGISTRATION FLOW
═══════════════════════════════════════════════════════════════════════════════

                          ┌─────────────────────┐
                          │   USER REGISTERS    │
                          │ Fill registration   │
                          │ form + submit       │
                          └──────────┬──────────┘
                                     │
                    POST /api/auth/register (email, password, role_id, etc.)
                                     │
                    ┌────────────────▼────────────────┐
                    │  BACKEND: Create User Account   │
                    │  - Create User record           │
                    │  - Create Student/Admin profile │
                    │  - Create StudentVerification   │
                    │    with status='Pending'        │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │  GENERATE & SEND OTP EMAIL      │
                    │  - Generate 6-digit code        │
                    │  - Store OTP in database        │
                    │  - Set otp_sent_at timestamp    │
                    │  - Send HTML email with code    │
                    │  - Set expiry timer (10 min)    │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │   RETURN REGISTRATION RESPONSE  │
                    │   {                             │
                    │     "next_step": "otp_verify"   │
                    │     "email": "user@example.com" │
                    │     "role_type": "student"      │
                    │   }                             │
                    └────────────────┬────────────────┘
                                     │
                          ┌──────────▼───────────┐
                          │ FRONTEND: REDIRECT   │
                          │ to verify-email-     │
                          │ otp.html?email=...   │
                          │ &role=student        │
                          └──────────┬───────────┘
                                     │

═══════════════════════════════════════════════════════════════════════════════
                        EMAIL VERIFICATION FLOW
═══════════════════════════════════════════════════════════════════════════════

                    ┌──────────────────────────────┐
                    │   OTP VERIFICATION PAGE      │
                    │ - Displays email address     │
                    │ - Shows 6 input boxes        │
                    │ - Displays 10-min countdown  │
                    └──────────┬───────────────────┘
                               │
                    USER enters 6-digit code
                               │
                    ┌──────────▼───────────────────┐
                    │   USER CLICKS VERIFY         │
                    │   POST /api/auth/verify-otp  │
                    │   {                          │
                    │     "email": "...",          │
                    │     "otp": "123456"          │
                    │   }                          │
                    └──────────┬───────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
   INVALID OTP          EXPIRED OTP           VALID OTP
   (Wrong code)      (> 10 minutes)       (Correct code)
        │                      │                      │
   Check OTP    Check otp_    Mark otp_verified
   matches      sent_at <      = True
   stored OTP   now - 10min    │
        │                      │          ┌──────────▼─────────┐
        │                      │          │ UPDATE DATABASE    │
   Increment                Mark as      │ - otp_verified=T   │
   otp_attempts            expired      │ - otp_verified_at  │
        │                      │         │   = now            │
   Too many?  ─YES──→ ╔════════╧═════╗ └──────────┬─────────┘
   (>5)                ║ SEND ERROR   ║            │
        │              ║ "OTP         ║   Send approval pending
      NO │             ║  Expired"    ║   email to user
        │              ╚═╤════════════╝            │
   ┌────▼────────┐      │          ┌──────────────▼──────────┐
   │ SEND ERROR  │      │          │  RETURN SUCCESS        │
   │ "Invalid    │      │          │  {                     │
   │  OTP"       │      │          │    "success": true,    │
   │ Attempts:   │      │          │    "email_verified":   │
   │ X remain    │      │          │      true,             │
   └─────┬───────┘      │          │    "next_step":        │
         │              │          │      "await_admin"     │
   Clear inputs      Clear       │  }                     │
   Focus first       inputs      └──────────┬─────────────┘
   box              Focus                  │
         │           first              FRONTEND:
         │           box                Show Success
         │              │                Message
         └──────┬───────┘                │
                │                  ┌─────▼──────────────┐
              USER               │  APPROVAL MESSAGE  │
              Retry               │  ✅ Email Verified │
                                  │  ⏳ Pending Admin  │
                                  │  Approval         │
                                  │  [Go to Login]    │
                                  └─────┬──────────────┘
                                        │
                                   USER clicks
                                   "Go to Login"
                                        │
                                  Redirect to
                                  index.html

═══════════════════════════════════════════════════════════════════════════════
                        ADMIN APPROVAL FLOW
═══════════════════════════════════════════════════════════════════════════════

                    ┌──────────────────────────┐
                    │  ADMIN LOGS INTO PORTAL  │
                    │  (Already approved admin)│
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │ VIEWS ADMIN DASHBOARD   │
                    │ "Pending Approvals" tab │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │ SEES STUDENT VERIFICATION QUEUE │
                    │ - Email verified ✅             │
                    │ - Awaiting approval             │
                    │ - Shows [APPROVE] [REJECT]      │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │ ADMIN CLICKS [APPROVE]          │
                    │ POST /api/admin/verify-student  │
                    │ {                               │
                    │   "student_id": 42,             │
                    │   "action": "approve"           │
                    │ }                               │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │ BACKEND UPDATES:                │
                    │ - User.is_verified = True       │
                    │ - StudentVerification.status    │
                    │   = "Verified"                  │
                    │ - Create access log entry       │
                    └──────────┬──────────────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │ SEND APPROVAL EMAIL TO USER     │
                    │ - Account approved              │
                    │ - Can now login                 │
                    │ - Portal access granted         │
                    └──────────┬──────────────────────┘
                               │

═══════════════════════════════════════════════════════════════════════════════
                      STUDENT LOGIN & PORTAL ACCESS
═══════════════════════════════════════════════════════════════════════════════

                    ┌──────────────────────────┐
                    │ USER RECEIVES APPROVAL   │
                    │ EMAIL - CAN NOW LOGIN    │
                    └──────────┬───────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │ GOES TO LOGIN PAGE      │
                    │ Enters email + password │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────────────┐
                    │ CHECK: User.is_verified = True? │
                    └──────────┬──────────────────────┘
                               │
                           YES │
                               │
                    ┌──────────▼──────────────────┐
                    │ ✅ LOGIN SUCCESSFUL         │
                    │ Generate JWT token          │
                    │ Store in localStorage       │
                    │ Redirect to dashboard       │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │ ✨ FULL PORTAL ACCESS       │
                    │ - Browse jobs               │
                    │ - Apply to positions        │
                    │ - Update profile            │
                    │ - View notifications        │
                    │ - Complete all features     │
                    └────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                      ERROR HANDLING FLOWS
═══════════════════════════════════════════════════════════════════════════════

SCENARIO 1: USER ENTERS WRONG OTP
───────────────────────────────────
Input: "000000" (wrong code)
        │
        ├─→ Backend validates: otp != stored_otp
        │
        ├─→ Increment otp_attempts++
        │
        ├─→ Check: otp_attempts > 5?
        │
        ├─→ NO: Send error
        │   "Incorrect code. 4 attempts remaining"
        │
        ├─→ Frontend: Clear inputs, refocus
        │
        └─→ User can retry


SCENARIO 2: USER DOESN'T ENTER OTP IN TIME (10 MIN EXPIRES)
───────────────────────────────────────────────────────────
Timer reaches 0:00
        │
        ├─→ Frontend: Disable verify button
        │
        ├─→ Show: "Code has expired"
        │
        ├─→ Backend: is_otp_valid() returns False
        │
        ├─→ If user tries to verify anyway:
        │   Send error "OTP has expired"
        │
        └─→ User clicks "Send code again"
            ├─→ New OTP generated
            ├─→ Email sent again
            └─→ Timer resets to 10 minutes


SCENARIO 3: USER FAILS 5 TIMES
───────────────────────────────
Attempt 1: Wrong
Attempt 2: Wrong
Attempt 3: Wrong
Attempt 4: Wrong
Attempt 5: Wrong (otp_attempts = 5)
        │
        ├─→ Backend: otp_attempts >= 5
        │
        ├─→ Send error: "Too many failed attempts"
        │
        ├─→ Frontend: Disable verify button
        │
        └─→ User MUST click "Send code again"
            ├─→ New OTP generated (resets counter)
            ├─→ Old OTP invalidated
            └─→ Can retry with new code


SCENARIO 4: USER MISSES APPROVAL PENDING MESSAGE
─────────────────────────────────────────────────
After OTP verification:
        │
        ├─→ User sees: "✅ Email Verified"
        │
        ├─→ User sees: "⏳ Pending Admin Approval"
        │
        ├─→ If user goes to login before approval:
        │   ├─→ Login with credentials
        │   ├─→ Backend checks: User.is_verified?
        │   ├─→ NO (still pending admin)
        │   └─→ Send error: "Account pending admin approval"
        │
        └─→ Must wait for admin to approve in dashboard

═══════════════════════════════════════════════════════════════════════════════
                      DATA FLOW DIAGRAM
═══════════════════════════════════════════════════════════════════════════════

                           DATABASE
                        ┌──────────────┐
                        │    users     │
                        ├──────────────┤
        ┌──────────────→ │ id           │
        │                │ email        │
        │                │ role_id      │
        │                │ is_verified  │ ←──────────── Changes to TRUE
        │                │              │              after OTP verified
        │                └──────────────┘              AND admin approves
        │
     User                    ┌──────────────────────────────┐
  Registration               │ student_verification        │
     Email                   ├──────────────────────────────┤
  Password                   │ id                           │
  Role                       │ student_id (FK)              │
                             │ status (Pending)             │
                             │ otp: "123456" ←─────────┐   │
                             │ otp_verified: False ←───┼─┐ │
                             │ otp_sent_at: NOW ←────┐ │ │ │
        ┌─────────────────── │ otp_verified_at: NULL │ │ │ │
        │                    │ otp_attempts: 0       │ │ │ │
        │                    └──────────────────────────┘ │ │ │
        │                                  ▲              │ │ │
        │                                  │              │ │ │
        │                         OTP Service            │ │ │
        │                    (otp_service.py)            │ │ │
        │                  ┌──────────────────┐          │ │ │
        │                  │ generate_otp()   │─────────→├─┘ │
        │                  │ send_otp_email() │─────────→│   │ OTP
        │                  │ is_otp_valid()   │         │   │ Verified
        │                  │                  │         │   │
        └─────────────────→│ verify_otp()     │─────────→├───┘
                           │                  │         │
                           └──────────────────┘         │
                                                        │
                                        After verification:
                                        └─→ Status: Verified
                                        └─→ is_verified: True
                                        └─→ User can login


═══════════════════════════════════════════════════════════════════════════════
```

---

## 🔄 Complete Timeline

```
T+0:00  → User clicks "Register"
T+0:15  → Form filled and submitted
T+0:20  → Backend creates user + OTP
T+0:25  → OTP email sent
T+0:30  → User redirected to OTP page
T+1:00  → User finds email, opens it
T+1:15  → User enters OTP code
T+1:20  → OTP verified ✅
T+1:25  → Approval pending message shown
T+1:30  → Admin notified of new user (optional webhook)
T+2:00  → Admin reviews user profile
T+3:00  → Admin clicks "Approve"
T+3:05  → Approval email sent to user
T+3:10  → User receives approval email
T+3:15  → User goes to login
T+3:20  → User logs in successfully ✅
T+3:25  → User accesses full portal ✨
```

---

**SYSTEM FLOW VISUALIZATION COMPLETE**

Status: ✅ Production Ready
