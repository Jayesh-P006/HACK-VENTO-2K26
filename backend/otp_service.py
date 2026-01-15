"""
OTP and Email Verification Module
Handles OTP generation, storage, sending, and verification
"""

import random
import string
from datetime import datetime, timedelta
from flask_mail import Message
from flask import current_app

def generate_otp(length=6):
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email, full_name, otp):
    """Send OTP verification email to user"""
    try:
        from email_service import mail
        
        subject = f'Silent Syntax Portal - Email Verification Code: {otp}'
        
        html_body = f"""
        <html style="font-family: Arial, sans-serif; background: #f5f5f5;">
            <body style="margin: 0; padding: 20px; background: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center; color: white;">
                        <h1 style="margin: 0; font-size: 28px;">Silent Syntax Portal</h1>
                        <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Email Verification</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 40px;">
                        <h2 style="color: #333; margin-top: 0;">Hello {full_name},</h2>
                        
                        <p style="color: #666; line-height: 1.6; font-size: 16px;">
                            Welcome to Silent Syntax Portal! We're excited to have you join our placement management system.
                        </p>
                        
                        <p style="color: #666; line-height: 1.6; font-size: 16px;">
                            To verify your email address, please use the following One-Time Password (OTP):
                        </p>
                        
                        <!-- OTP Box -->
                        <div style="background: #f0f4ff; border-left: 4px solid #667eea; padding: 20px; margin: 30px 0; border-radius: 5px;">
                            <p style="margin: 0; color: #666; font-size: 14px; text-transform: uppercase;">Your Verification Code</p>
                            <h1 style="margin: 10px 0 0 0; color: #667eea; font-size: 36px; letter-spacing: 2px; font-family: monospace;">{otp}</h1>
                        </div>
                        
                        <p style="color: #999; font-size: 14px;">
                            <strong>Note:</strong> This code is valid for 10 minutes. Do not share this code with anyone.
                        </p>
                        
                        <p style="color: #666; line-height: 1.6; font-size: 16px;">
                            After verifying your email, your account will be pending admin approval before you can access the portal.
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        
                        <p style="color: #999; font-size: 14px; margin: 0;">
                            If you didn't request this verification, please ignore this email.
                        </p>
                        <p style="color: #999; font-size: 14px; margin: 10px 0 0 0;">
                            <strong>Never share your OTP with anyone, including support staff.</strong>
                        </p>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                        <p style="margin: 0; color: #999; font-size: 12px;">
                            © 2026 Silent Syntax Portal. All rights reserved.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
Silent Syntax Portal - Email Verification

Hello {full_name},

Welcome to Silent Syntax Portal! To verify your email address, please use the following One-Time Password (OTP):

{otp}

This code is valid for 10 minutes. Do not share this code with anyone.

After verifying your email, your account will be pending admin approval before you can access the portal.

If you didn't request this verification, please ignore this email.

© 2026 Silent Syntax Portal
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        print(f'[OTP] Email sent to {email} with OTP: {otp}')
        return True
        
    except Exception as e:
        print(f'[OTP] Failed to send email to {email}: {str(e)}')
        return False


def is_otp_valid(otp_record):
    """Check if OTP is still valid (not expired)"""
    if not otp_record or not otp_record.otp_sent_at:
        return False
    
    # OTP is valid for 10 minutes
    expiry_time = otp_record.otp_sent_at + timedelta(minutes=10)
    return datetime.utcnow() < expiry_time


def send_approval_pending_email(email, full_name, role_type):
    """Send email notifying user that email is verified, pending admin approval"""
    try:
        from email_service import mail
        
        role_text = "student" if role_type == "student" else "admin" if role_type == "admin" else "company"
        
        subject = 'Silent Syntax Portal - Email Verified, Pending Admin Approval'
        
        html_body = f"""
        <html style="font-family: Arial, sans-serif; background: #f5f5f5;">
            <body style="margin: 0; padding: 20px; background: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center; color: white;">
                        <h1 style="margin: 0; font-size: 28px;">✅ Email Verified</h1>
                        <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">Pending Admin Approval</p>
                    </div>
                    
                    <!-- Content -->
                    <div style="padding: 40px;">
                        <h2 style="color: #333; margin-top: 0;">Hello {full_name},</h2>
                        
                        <div style="background: #e8f5e9; border-left: 4px solid #4CAF50; padding: 20px; margin: 20px 0; border-radius: 5px;">
                            <p style="margin: 0; color: #2e7d32; font-size: 16px;">
                                ✅ Your email has been successfully verified!
                            </p>
                        </div>
                        
                        <p style="color: #666; line-height: 1.6; font-size: 16px;">
                            Thank you for verifying your email address. Your {role_text} account is now pending approval from our admin team.
                        </p>
                        
                        <div style="background: #fff3cd; border-left: 4px solid #ff9800; padding: 20px; margin: 20px 0; border-radius: 5px;">
                            <p style="margin: 0; color: #f57c00; font-size: 16px;">
                                <strong>⏳ What's Next?</strong>
                            </p>
                            <p style="margin: 10px 0 0 0; color: #666; font-size: 14px;">
                                Our admin team will review your account and send you an approval email within 24 hours. Once approved, you'll be able to access the full portal.
                            </p>
                        </div>
                        
                        <p style="color: #666; line-height: 1.6; font-size: 16px;">
                            In the meantime, you can:
                        </p>
                        <ul style="color: #666; line-height: 1.8; font-size: 16px;">
                            <li>Check your email for approval notification</li>
                            <li>Update your profile information</li>
                            <li>Review our help documentation</li>
                        </ul>
                        
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        
                        <p style="color: #999; font-size: 14px; margin: 0;">
                            If you have any questions, please contact our support team.
                        </p>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background: #f9f9f9; padding: 20px; text-align: center; border-top: 1px solid #eee;">
                        <p style="margin: 0; color: #999; font-size: 12px;">
                            © 2026 Silent Syntax Portal. All rights reserved.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
Silent Syntax Portal - Email Verified, Pending Admin Approval

Hello {full_name},

✅ Your email has been successfully verified!

Thank you for verifying your email address. Your {role_text} account is now pending approval from our admin team.

⏳ What's Next?
Our admin team will review your account and send you an approval email within 24 hours. Once approved, you'll be able to access the full portal.

In the meantime, you can:
- Check your email for approval notification
- Update your profile information
- Review our help documentation

If you have any questions, please contact our support team.

© 2026 Silent Syntax Portal
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_body,
            body=text_body
        )
        
        mail.send(msg)
        print(f'[OTP] Approval pending email sent to {email}')
        return True
        
    except Exception as e:
        print(f'[OTP] Failed to send approval pending email to {email}: {str(e)}')
        return False
