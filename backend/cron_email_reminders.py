"""
Cron Job Setup for Email Reminders
This script can be scheduled to run daily to send automated email notifications

For Railway/Heroku: Use Railway Cron or external cron job services like cron-job.org
For local/self-hosted: Use system cron or Windows Task Scheduler

Linux Cron Example:
# Run daily at 9 AM
0 9 * * * cd /path/to/backend && python cron_email_reminders.py

Windows Task Scheduler:
Schedule to run python cron_email_reminders.py daily at 9 AM
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment
from dotenv import load_dotenv
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

# Import app for context
from app import app, db

# Import reminder functions
from email_reminder_engine import (
    send_deadline_reminders,
    send_interview_reminders,
    send_post_interview_feedback_requests
)

def run_daily_email_jobs():
    """Run all daily email reminder jobs"""
    print("=" * 60)
    print("🔄 Starting Daily Email Reminder Jobs")
    print(f"⏰ Time: {__import__('datetime').datetime.now()}")
    print("=" * 60)
    
    with app.app_context():
        # 1. Send deadline alerts
        print("\n📅 Task 1: Deadline Alerts")
        print("-" * 60)
        deadline_success = send_deadline_reminders()
        print(f"{'✅ Success' if deadline_success else '❌ Failed'}: Deadline alerts")
        
        # 2. Send interview reminders
        print("\n📞 Task 2: Interview Reminders")
        print("-" * 60)
        interview_success = send_interview_reminders()
        print(f"{'✅ Success' if interview_success else '❌ Failed'}: Interview reminders")
        
        # 3. Send feedback requests
        print("\n📝 Task 3: Feedback Requests")
        print("-" * 60)
        feedback_success = send_post_interview_feedback_requests()
        print(f"{'✅ Success' if feedback_success else '❌ Failed'}: Feedback requests")
        
        print("\n" + "=" * 60)
        print("✅ Daily Email Reminder Jobs Completed")
        print("=" * 60)
        
        return {
            'deadline_alerts': deadline_success,
            'interview_reminders': interview_success,
            'feedback_requests': feedback_success,
            'all_success': all([deadline_success, interview_success, feedback_success])
        }

if __name__ == '__main__':
    try:
        results = run_daily_email_jobs()
        sys.exit(0 if results['all_success'] else 1)
    except Exception as e:
        print(f"\n❌ Fatal Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
