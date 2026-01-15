"""
Email Service for Silent Syntax Portal
Handles all email communications including welcome emails, notifications, and alerts
"""
import os
from datetime import datetime
from flask import render_template_string
from flask_mail import Mail, Message
from threading import Thread

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app configuration"""
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
    mail.init_app(app)
    return mail


def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            print(f"✉️ Email sent successfully to {msg.recipients}")
        except Exception as e:
            print(f"❌ Email send failed: {str(e)}")


def send_email(subject, recipients, html_body, text_body=None):
    """
    Send email with HTML and optional text body
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        html_body: HTML formatted email body
        text_body: Plain text fallback (optional)
    """
    from app import app  # Import here to avoid circular imports
    
    if not isinstance(recipients, list):
        recipients = [recipients]
    
    msg = Message(
        subject=subject,
        recipients=recipients,
        html=html_body,
        body=text_body or "Please view this email in HTML format."
    )
    
    # Send asynchronously to avoid blocking
    Thread(target=send_async_email, args=(app, msg)).start()


# ==================== EMAIL TEMPLATES ====================

def get_email_template(content, title="Silent Syntax Portal"):
    """Base email template wrapper"""
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background: #ffffff;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .email-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .email-header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 600;
            }}
            .email-body {{
                padding: 30px;
            }}
            .email-footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #6c757d;
                border-top: 1px solid #e9ecef;
            }}
            .button {{
                display: inline-block;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 600;
                margin: 15px 0;
            }}
            .info-box {{
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
            .highlight {{
                color: #667eea;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="email-header">
                <h1>🎓 Silent Syntax Portal</h1>
            </div>
            <div class="email-body">
                {content}
            </div>
            <div class="email-footer">
                <p>© 2026 Silent Syntax Portal. All rights reserved.</p>
                <p>This is an automated email. Please do not reply to this message.</p>
            </div>
        </div>
    </body>
    </html>
    """


def send_welcome_email(user_email, full_name, role="Student"):
    """Send welcome email after admin approval"""
    content = f"""
        <h2>Welcome to Silent Syntax Portal! 🎉</h2>
        <p>Dear <strong>{full_name}</strong>,</p>
        <p>Congratulations! Your account has been <span class="highlight">approved by our admin team</span>.</p>
        
        <div class="info-box">
            <p><strong>Your Account Details:</strong></p>
            <p>📧 Email: {user_email}<br>
            👤 Role: {role}</p>
        </div>
        
        <p>You can now access all features of the Silent Syntax Portal:</p>
        <ul>
            <li>✅ Browse job opportunities from top companies</li>
            <li>✅ Apply to positions matching your profile</li>
            <li>✅ Track your applications in real-time</li>
            <li>✅ Get personalized learning roadmaps</li>
            <li>✅ Receive instant notifications</li>
        </ul>
        
        <div style="text-align: center;">
            <a href="https://hack-vento-2k26-production.up.railway.app/portal/index.html" class="button">
                Login to Your Dashboard
            </a>
        </div>
        
        <p>If you have any questions or need assistance, feel free to reach out to our support team.</p>
        
        <p>Best regards,<br>
        <strong>Silent Syntax Team</strong></p>
    """
    
    html_body = get_email_template(content, "Welcome to Silent Syntax Portal")
    send_email(
        subject="🎉 Welcome to Silent Syntax Portal - Account Approved!",
        recipients=user_email,
        html_body=html_body
    )


def send_deadline_alert(user_email, full_name, job_title, company_name, deadline_date, days_remaining):
    """Send deadline reminder for job application"""
    content = f"""
        <h2>⏰ Application Deadline Alert</h2>
        <p>Dear <strong>{full_name}</strong>,</p>
        <p>This is a friendly reminder about an upcoming application deadline:</p>
        
        <div class="info-box">
            <p><strong>📋 Job Details:</strong></p>
            <p><strong>Position:</strong> {job_title}<br>
            <strong>Company:</strong> {company_name}<br>
            <strong>Deadline:</strong> {deadline_date}<br>
            <strong>⏳ Time Remaining:</strong> <span class="highlight">{days_remaining} days</span></p>
        </div>
        
        <p>Don't miss this opportunity! Make sure to submit your application before the deadline.</p>
        
        <div style="text-align: center;">
            <a href="https://hack-vento-2k26-production.up.railway.app/portal/student.html" class="button">
                View Job & Apply Now
            </a>
        </div>
        
        <p>Best of luck with your application!</p>
        
        <p>Best regards,<br>
        <strong>Silent Syntax Team</strong></p>
    """
    
    html_body = get_email_template(content, "Application Deadline Alert")
    send_email(
        subject=f"⏰ Deadline Alert: {job_title} at {company_name} - {days_remaining} days left!",
        recipients=user_email,
        html_body=html_body
    )


def send_shortlist_notification(user_email, full_name, job_title, company_name, next_round=None):
    """Send notification when student is shortlisted"""
    content = f"""
        <h2>🎊 Congratulations! You've Been Shortlisted!</h2>
        <p>Dear <strong>{full_name}</strong>,</p>
        <p>Great news! Your application has been shortlisted for the next round.</p>
        
        <div class="info-box">
            <p><strong>📋 Application Details:</strong></p>
            <p><strong>Position:</strong> {job_title}<br>
            <strong>Company:</strong> {company_name}<br>
            {f'<strong>Next Round:</strong> {next_round}' if next_round else ''}</p>
        </div>
        
        <p>This is a significant step forward in your application process. The company is interested in learning more about you!</p>
        
        <p><strong>What's Next?</strong></p>
        <ul>
            <li>Keep an eye on your email for interview schedule</li>
            <li>Review the company and job requirements</li>
            <li>Prepare your interview materials</li>
            <li>Stay updated on your dashboard</li>
        </ul>
        
        <div style="text-align: center;">
            <a href="https://hack-vento-2k26-production.up.railway.app/portal/student.html" class="button">
                View Application Status
            </a>
        </div>
        
        <p>Best of luck for the next round!</p>
        
        <p>Best regards,<br>
        <strong>Silent Syntax Team</strong></p>
    """
    
    html_body = get_email_template(content, "Shortlisted for Interview")
    send_email(
        subject=f"🎊 You've Been Shortlisted! - {job_title} at {company_name}",
        recipients=user_email,
        html_body=html_body
    )


def send_interview_schedule(user_email, full_name, job_title, company_name, interview_date, interview_time, interview_mode, interview_link=None, interview_location=None):
    """Send interview schedule notification"""
    location_info = f"<strong>Location:</strong> {interview_location}<br>" if interview_location else ""
    link_info = f"<strong>Meeting Link:</strong> <a href='{interview_link}'>{interview_link}</a><br>" if interview_link else ""
    
    content = f"""
        <h2>📅 Interview Scheduled</h2>
        <p>Dear <strong>{full_name}</strong>,</p>
        <p>Your interview has been scheduled! Please find the details below:</p>
        
        <div class="info-box">
            <p><strong>📋 Interview Details:</strong></p>
            <p><strong>Position:</strong> {job_title}<br>
            <strong>Company:</strong> {company_name}<br>
            <strong>Date:</strong> {interview_date}<br>
            <strong>Time:</strong> {interview_time}<br>
            <strong>Mode:</strong> {interview_mode}<br>
            {location_info}
            {link_info}</p>
        </div>
        
        <p><strong>⚠️ Important Reminders:</strong></p>
        <ul>
            <li>Join 5-10 minutes before the scheduled time</li>
            <li>Test your internet connection and devices beforehand</li>
            <li>Keep your resume and documents ready</li>
            <li>Dress professionally</li>
            <li>Prepare questions about the role and company</li>
        </ul>
        
        <div style="text-align: center;">
            <a href="https://hack-vento-2k26-production.up.railway.app/portal/student.html" class="button">
                View Full Details
            </a>
        </div>
        
        <p>Good luck with your interview! We're rooting for you! 🍀</p>
        
        <p>Best regards,<br>
        <strong>Silent Syntax Team</strong></p>
    """
    
    html_body = get_email_template(content, "Interview Scheduled")
    send_email(
        subject=f"📅 Interview Scheduled: {job_title} at {company_name} - {interview_date}",
        recipients=user_email,
        html_body=html_body
    )


def send_offer_letter(user_email, full_name, job_title, company_name, package, joining_date=None):
    """Send offer letter notification"""
    joining_info = f"<strong>Joining Date:</strong> {joining_date}<br>" if joining_date else ""
    
    content = f"""
        <h2>🎉 Congratulations! You Have an Offer!</h2>
        <p>Dear <strong>{full_name}</strong>,</p>
        <p><strong>Congratulations!</strong> We're thrilled to inform you that you have received an offer letter!</p>
        
        <div class="info-box" style="border-left-color: #28a745;">
            <p><strong>🎊 Offer Details:</strong></p>
            <p><strong>Position:</strong> {job_title}<br>
            <strong>Company:</strong> {company_name}<br>
            <strong>Package:</strong> <span class="highlight" style="color: #28a745; font-size: 18px;">₹{package}</span><br>
            {joining_info}</p>
        </div>
        
        <p>This is a remarkable achievement and a testament to your hard work and skills. The company is excited to have you on board!</p>
        
        <p><strong>Next Steps:</strong></p>
        <ul>
            <li>Check your dashboard for the complete offer letter</li>
            <li>Review the terms and conditions carefully</li>
            <li>Contact the company HR if you have any questions</li>
            <li>Respond to the offer within the given timeframe</li>
        </ul>
        
        <div style="text-align: center;">
            <a href="https://hack-vento-2k26-production.up.railway.app/portal/student.html" class="button">
                View Offer Letter
            </a>
        </div>
        
        <p>Once again, congratulations on this achievement!</p>
        
        <p>Best regards,<br>
        <strong>Silent Syntax Team</strong></p>
    """
    
    html_body = get_email_template(content, "Offer Letter Received")
    send_email(
        subject=f"🎉 Offer Letter: {job_title} at {company_name} - Congratulations!",
        recipients=user_email,
        html_body=html_body
    )


def send_feedback_request(user_email, full_name, job_title, company_name):
    """Send post-interview feedback request"""
    content = f"""
        <h2>📝 Share Your Interview Experience</h2>
        <p>Dear <strong>{full_name}</strong>,</p>
        <p>Thank you for participating in the interview process with <strong>{company_name}</strong> for the <strong>{job_title}</strong> position.</p>
        
        <div class="info-box">
            <p>We'd love to hear about your interview experience! Your feedback helps us:</p>
            <ul>
                <li>Improve the placement process</li>
                <li>Help other students prepare better</li>
                <li>Build a knowledge base of company experiences</li>
                <li>Provide valuable insights to future candidates</li>
            </ul>
        </div>
        
        <p>Please take a few minutes to share your experience, including:</p>
        <ul>
            <li>Interview rounds and format</li>
            <li>Types of questions asked</li>
            <li>Overall difficulty level</li>
            <li>Tips for future candidates</li>
        </ul>
        
        <div style="text-align: center;">
            <a href="https://hack-vento-2k26-production.up.railway.app/portal/student.html" class="button">
                Share Your Experience
            </a>
        </div>
        
        <p>Thank you for contributing to our community!</p>
        
        <p>Best regards,<br>
        <strong>Silent Syntax Team</strong></p>
    """
    
    html_body = get_email_template(content, "Interview Feedback Request")
    send_email(
        subject=f"📝 Share Your Interview Experience - {job_title} at {company_name}",
        recipients=user_email,
        html_body=html_body
    )


def send_application_status_update(user_email, full_name, job_title, company_name, new_status, message=None):
    """Send general application status update"""
    status_messages = {
        'Applied': 'Your application has been submitted successfully.',
        'Under Review': 'Your application is currently under review by the company.',
        'Shortlisted': 'Congratulations! You have been shortlisted.',
        'Interview': 'You have been scheduled for an interview.',
        'Selected': 'Congratulations! You have been selected!',
        'Rejected': 'Unfortunately, your application was not selected this time.',
        'On Hold': 'Your application is currently on hold.',
    }
    
    status_icon = {
        'Applied': '✅',
        'Under Review': '🔍',
        'Shortlisted': '🎊',
        'Interview': '📅',
        'Selected': '🎉',
        'Rejected': '📋',
        'On Hold': '⏸️',
    }
    
    icon = status_icon.get(new_status, '📌')
    default_message = status_messages.get(new_status, f'Your application status has been updated to: {new_status}')
    
    content = f"""
        <h2>{icon} Application Status Update</h2>
        <p>Dear <strong>{full_name}</strong>,</p>
        <p>Your application status has been updated:</p>
        
        <div class="info-box">
            <p><strong>📋 Application Details:</strong></p>
            <p><strong>Position:</strong> {job_title}<br>
            <strong>Company:</strong> {company_name}<br>
            <strong>New Status:</strong> <span class="highlight">{new_status}</span></p>
        </div>
        
        <p>{message or default_message}</p>
        
        <div style="text-align: center;">
            <a href="https://hack-vento-2k26-production.up.railway.app/portal/student.html" class="button">
                View Application Details
            </a>
        </div>
        
        <p>Stay updated by checking your dashboard regularly.</p>
        
        <p>Best regards,<br>
        <strong>Silent Syntax Team</strong></p>
    """
    
    html_body = get_email_template(content, "Application Status Update")
    send_email(
        subject=f"{icon} Status Update: {job_title} at {company_name} - {new_status}",
        recipients=user_email,
        html_body=html_body
    )
