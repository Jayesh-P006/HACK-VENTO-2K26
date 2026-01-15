# Email Engine Setup and Usage Guide

## ✅ Implementation Complete!

The complete email notification system has been implemented with the following features:

### 📧 Email Features Implemented

1. **Welcome Emails**
   - Sent automatically when admin approves student registration
   - Includes account details and login link
   
2. **Deadline Alerts**
   - Automated reminders 7, 3, and 1 day before job application deadlines
   - Only sent to eligible students who haven't applied yet
   
3. **Shortlist Notifications**
   - Instant email when student is shortlisted
   - Includes next steps and preparation tips
   
4. **Interview Schedule**
   - Email with complete interview details
   - Date, time, mode, location/link
   - Interview preparation checklist
   
5. **Offer Letters**
   - Congratulatory email with package details
   - Next steps for accepting the offer
   
6. **Post-Interview Feedback**
   - Request feedback 24 hours after interview
   - Helps build community knowledge base
   
7. **Status Updates**
   - Generic status change notifications
   - Custom messages from company

---

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install Flask-Mail
```

### 2. Configure Email Settings

Create/Update your `.env` file with email configuration:

```env
# Email Configuration (Gmail Example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**For Gmail:**
1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the app password (not your regular password)

**Other Email Providers:**
- **Outlook/Office365**: `smtp.office365.com`, Port 587
- **SendGrid**: `smtp.sendgrid.net`, Port 587
- **AWS SES**: Regional endpoint, Port 587

### 3. Start the Backend
```bash
python app.py
```

---

## 📬 How to Use

### Automatic Email Triggers

1. **Welcome Email**
   - Automatically sent when admin approves student from verification queue
   - Endpoint: `POST /api/admin/verification/{id}/approve`

2. **Status Update Emails**
   - Automatically sent when company updates application status
   - Endpoint: `PUT /api/company/application-status`
   - Triggers for: Shortlisted, Offered, Interview, Rejected, etc.

### Manual Email Campaigns (Admin Only)

Admin can manually trigger email reminders:

```bash
# Trigger deadline alerts
POST /api/email-reminders/trigger-deadline-alerts
Headers: Authorization: Bearer <admin_token>

# Trigger interview reminders
POST /api/email-reminders/trigger-interview-reminders

# Trigger feedback requests
POST /api/email-reminders/trigger-feedback-requests

# Trigger all reminders at once
POST /api/email-reminders/trigger-all

# Check email configuration status
GET /api/email-reminders/status
```

### Automated Daily Jobs

Set up cron jobs to run email reminders automatically:

#### Railway/Heroku (Cloud Platform)
Use Railway Cron or external services like cron-job.org to hit the API endpoints daily

#### Linux/Mac Cron
```bash
crontab -e

# Add this line to run at 9 AM daily
0 9 * * * cd /path/to/backend && python cron_email_reminders.py
```

#### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set to run daily at 9 AM
4. Action: Start Program
5. Program: `python`
6. Arguments: `cron_email_reminders.py`
7. Start in: `F:\2. HACKVENTO 2K26\backend`

---

## 🎨 Email Templates

All emails use a professional responsive template with:
- Silent Syntax branding
- Gradient headers
- Responsive design
- Call-to-action buttons
- Professional footer

Templates included:
- `send_welcome_email()` - Welcome new users
- `send_deadline_alert()` - Job deadline reminders
- `send_shortlist_notification()` - Shortlist congrats
- `send_interview_schedule()` - Interview details
- `send_offer_letter()` - Offer congratulations
- `send_feedback_request()` - Post-interview feedback
- `send_application_status_update()` - Generic status updates

---

## 🔍 Testing Emails

### Test Welcome Email
```python
from email_service import send_welcome_email

send_welcome_email(
    user_email="test@example.com",
    full_name="Test Student",
    role="Student"
)
```

### Test All Reminder Jobs
```bash
cd backend
python cron_email_reminders.py
```

### Check Configuration
```bash
curl -X GET http://localhost:5000/api/email-reminders/status \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## 📊 Email Flow Diagram

```
USER REGISTRATION
    ↓
Admin Approval → ✉️ Welcome Email
    ↓
USER ACTIVE
    ↓
7 Days Before Deadline → ✉️ Deadline Alert
3 Days Before Deadline → ✉️ Deadline Alert
1 Day Before Deadline → ✉️ Deadline Alert
    ↓
APPLICATION SUBMITTED
    ↓
Status: Shortlisted → ✉️ Shortlist Notification
    ↓
Interview Scheduled → ✉️ Interview Details (24h before)
    ↓
Interview Complete → ✉️ Feedback Request (24h after)
    ↓
Status: Offered → ✉️ Offer Letter
    ↓
Any Status Change → ✉️ Status Update
```

---

## 🛠️ Troubleshooting

### Emails Not Sending?
1. Check `.env` file has correct SMTP settings
2. Verify Gmail app password (not regular password)
3. Check console logs for error messages
4. Test SMTP connection manually
5. Ensure firewall allows outbound SMTP (Port 587)

### Gmail Blocking Emails?
1. Enable "Less secure app access" (if not using app password)
2. Use App-Specific Password
3. Check Gmail's "Recently blocked sign-in" attempts

### Testing Email in Development
Use a test email service like:
- Mailtrap.io (catches all emails)
- Ethereal.email (temporary inbox)
- Gmail test account

---

## 📝 Files Created

1. `backend/email_service.py` - Core email functions and templates
2. `backend/email_reminder_engine.py` - Automated reminder logic
3. `backend/email_reminder_routes.py` - API endpoints for manual triggers
4. `backend/cron_email_reminders.py` - Cron job script
5. `backend/.env.example` - Updated with email configuration
6. `backend/requirements.txt` - Added Flask-Mail dependency

---

## 🚀 Deployment Notes

### For Railway
1. Add email environment variables in Railway dashboard
2. Set up Railway Cron or use external cron service
3. Emails will work automatically on deployment

### For Heroku
1. Add config vars for email settings
2. Use Heroku Scheduler add-on for cron jobs
3. Command: `python cron_email_reminders.py`

### For Vercel/Serverless
- Email sending works but cron jobs need external service
- Use Vercel Cron or cron-job.org for scheduled tasks
- API endpoints for manual triggers work fine

---

## ✅ All Done!

The email engine is fully integrated and ready to use. Just configure your SMTP settings and emails will start flowing automatically! 🎉
