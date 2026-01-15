# Quick Start: Email Engine Setup

## 1. Install Flask-Mail
```bash
cd backend
pip install Flask-Mail
```

## 2. Configure Email (Add to your .env file)

```env
# Gmail Configuration (Recommended)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### How to Get Gmail App Password:
1. Go to Google Account: https://myaccount.google.com/
2. Security → 2-Step Verification (Enable if not enabled)
3. App passwords: https://myaccount.google.com/apppasswords
4. Select "Mail" and "Other (Custom name)"
5. Copy the 16-character password
6. Use this password in MAIL_PASSWORD

## 3. Restart Backend
```bash
python app.py
```

## ✅ Done! Emails Will Work Automatically

### Automatic Emails:
- ✉️ Welcome email when admin approves student
- ✉️ Status updates when company changes application status
- ✉️ Shortlist, Interview, Offer notifications

### Manual Triggers (Admin Only):
```bash
POST /api/email-reminders/trigger-deadline-alerts
POST /api/email-reminders/trigger-interview-reminders
POST /api/email-reminders/trigger-feedback-requests
```

### For Automated Daily Reminders:
Run `cron_email_reminders.py` daily using cron or Task Scheduler

See EMAIL_SETUP_GUIDE.md for detailed documentation.
