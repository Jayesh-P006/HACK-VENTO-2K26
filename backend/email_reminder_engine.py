"""
Email Reminder Engine - Background Tasks
Automated email notifications for deadlines, interviews, and status updates
"""
from datetime import datetime, timedelta
from models import Job, Application, Student, User, db
from email_service import (
    send_deadline_alert,
    send_interview_schedule,
    send_feedback_request
)

def send_deadline_reminders():
    """
    Send deadline alerts to students for jobs with upcoming deadlines
    Triggers: 7 days, 3 days, 1 day before deadline
    """
    try:
        today = datetime.now().date()
        
        # Check for deadlines in 7, 3, and 1 days
        deadline_intervals = [
            (7, "7 days"),
            (3, "3 days"),
            (1, "1 day")
        ]
        
        for days, label in deadline_intervals:
            target_date = today + timedelta(days=days)
            
            # Find jobs with deadlines on target date
            jobs = Job.query.filter(
                Job.status == 'Active',
                Job.application_deadline == target_date
            ).all()
            
            for job in jobs:
                # Get all eligible students who haven't applied yet
                applied_student_ids = [app.student_id for app in Application.query.filter_by(job_id=job.id).all()]
                
                # Get eligible students based on CGPA and branch
                eligible_students = Student.query.filter(
                    Student.cgpa >= (job.min_cgpa or 0),
                    ~Student.id.in_(applied_student_ids) if applied_student_ids else True
                ).all()
                
                # Send reminder to eligible students
                for student in eligible_students:
                    if student.user and student.user.email:
                        try:
                            send_deadline_alert(
                                user_email=student.user.email,
                                full_name=student.full_name,
                                job_title=job.title,
                                company_name=job.company.company_name,
                                deadline_date=job.application_deadline.strftime('%B %d, %Y'),
                                days_remaining=days
                            )
                            print(f"📧 Deadline alert sent to {student.full_name} for {job.title}")
                        except Exception as e:
                            print(f"❌ Failed to send deadline alert: {str(e)}")
        
        print(f"✅ Deadline reminder job completed at {datetime.now()}")
        return True
        
    except Exception as e:
        print(f"❌ Deadline reminder job failed: {str(e)}")
        return False


def send_interview_reminders():
    """
    Send interview reminders 24 hours before scheduled interview
    """
    try:
        from models import HiringRound, ApplicationRound
        
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        # Find application rounds with interviews scheduled for tomorrow
        upcoming_interviews = ApplicationRound.query.join(HiringRound).filter(
            ApplicationRound.scheduled_date == tomorrow,
            ApplicationRound.status.in_(['Scheduled', 'Upcoming'])
        ).all()
        
        for app_round in upcoming_interviews:
            application = app_round.application
            student = application.student
            job = application.job
            hiring_round = app_round.hiring_round
            
            if student.user and student.user.email:
                try:
                    send_interview_schedule(
                        user_email=student.user.email,
                        full_name=student.full_name,
                        job_title=job.title,
                        company_name=job.company.company_name,
                        interview_date=app_round.scheduled_date.strftime('%B %d, %Y'),
                        interview_time=app_round.scheduled_time.strftime('%I:%M %p') if app_round.scheduled_time else 'TBD',
                        interview_mode=hiring_round.round_type,
                        interview_link=getattr(app_round, 'meeting_link', None),
                        interview_location=getattr(app_round, 'location', None)
                    )
                    print(f"📧 Interview reminder sent to {student.full_name}")
                except Exception as e:
                    print(f"❌ Failed to send interview reminder: {str(e)}")
        
        print(f"✅ Interview reminder job completed at {datetime.now()}")
        return True
        
    except Exception as e:
        print(f"❌ Interview reminder job failed: {str(e)}")
        return False


def send_post_interview_feedback_requests():
    """
    Send feedback request 24 hours after interview completion
    """
    try:
        from models import ApplicationRound
        
        yesterday = datetime.now().date() - timedelta(days=1)
        
        # Find completed interviews from yesterday
        completed_interviews = ApplicationRound.query.filter(
            ApplicationRound.scheduled_date == yesterday,
            ApplicationRound.status == 'Completed',
            ApplicationRound.feedback_submitted == False  # noqa
        ).all()
        
        for app_round in completed_interviews:
            application = app_round.application
            student = application.student
            job = application.job
            
            if student.user and student.user.email:
                try:
                    send_feedback_request(
                        user_email=student.user.email,
                        full_name=student.full_name,
                        job_title=job.title,
                        company_name=job.company.company_name
                    )
                    print(f"📧 Feedback request sent to {student.full_name}")
                except Exception as e:
                    print(f"❌ Failed to send feedback request: {str(e)}")
        
        print(f"✅ Feedback request job completed at {datetime.now()}")
        return True
        
    except Exception as e:
        print(f"❌ Feedback request job failed: {str(e)}")
        return False


# Manual trigger functions for immediate use
def trigger_deadline_reminders_manual():
    """Manually trigger deadline reminders (for testing or immediate need)"""
    from app import app
    with app.app_context():
        return send_deadline_reminders()


def trigger_interview_reminders_manual():
    """Manually trigger interview reminders (for testing or immediate need)"""
    from app import app
    with app.app_context():
        return send_interview_reminders()


def trigger_feedback_requests_manual():
    """Manually trigger feedback requests (for testing or immediate need)"""
    from app import app
    with app.app_context():
        return send_post_interview_feedback_requests()


if __name__ == '__main__':
    # For testing purposes
    print("🔄 Running email reminder engine...")
    trigger_deadline_reminders_manual()
    trigger_interview_reminders_manual()
    trigger_feedback_requests_manual()
    print("✅ Email reminder engine completed")
