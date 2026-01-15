"""
Email Reminder Routes - Admin can trigger email campaigns manually
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User
from email_reminder_engine import (
    send_deadline_reminders,
    send_interview_reminders,
    send_post_interview_feedback_requests
)

email_reminder_bp = Blueprint('email_reminders', __name__, url_prefix='/api/email-reminders')

def get_user_id():
    """Convert JWT identity to user_id"""
    identity = get_jwt_identity()
    return int(identity) if identity else None

def check_admin(user_id):
    """Verify user is admin"""
    user = User.query.get(user_id)
    return user and user.role_id == 3


@email_reminder_bp.route('/trigger-deadline-alerts', methods=['POST'])
@jwt_required()
def trigger_deadline_alerts():
    """Manually trigger deadline reminder emails"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized - Admin access only'}), 403
        
        result = send_deadline_reminders()
        
        return jsonify({
            'success': result,
            'message': 'Deadline reminder emails triggered successfully' if result else 'Deadline reminder job failed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@email_reminder_bp.route('/trigger-interview-reminders', methods=['POST'])
@jwt_required()
def trigger_interview_reminders_route():
    """Manually trigger interview reminder emails"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized - Admin access only'}), 403
        
        result = send_interview_reminders()
        
        return jsonify({
            'success': result,
            'message': 'Interview reminder emails triggered successfully' if result else 'Interview reminder job failed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@email_reminder_bp.route('/trigger-feedback-requests', methods=['POST'])
@jwt_required()
def trigger_feedback_requests_route():
    """Manually trigger post-interview feedback request emails"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized - Admin access only'}), 403
        
        result = send_post_interview_feedback_requests()
        
        return jsonify({
            'success': result,
            'message': 'Feedback request emails triggered successfully' if result else 'Feedback request job failed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@email_reminder_bp.route('/trigger-all', methods=['POST'])
@jwt_required()
def trigger_all_reminders():
    """Trigger all email reminder jobs"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized - Admin access only'}), 403
        
        deadline_result = send_deadline_reminders()
        interview_result = send_interview_reminders()
        feedback_result = send_post_interview_feedback_requests()
        
        return jsonify({
            'success': True,
            'results': {
                'deadline_alerts': deadline_result,
                'interview_reminders': interview_result,
                'feedback_requests': feedback_result
            },
            'message': 'All email reminder jobs triggered'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@email_reminder_bp.route('/status', methods=['GET'])
@jwt_required()
def get_email_status():
    """Get email service status and configuration"""
    try:
        user_id = get_user_id()
        if not check_admin(user_id):
            return jsonify({'error': 'Unauthorized - Admin access only'}), 403
        
        import os
        
        return jsonify({
            'success': True,
            'email_configured': bool(os.getenv('MAIL_USERNAME')),
            'mail_server': os.getenv('MAIL_SERVER', 'Not configured'),
            'mail_port': os.getenv('MAIL_PORT', 'Not configured'),
            'mail_use_tls': os.getenv('MAIL_USE_TLS', 'Not configured'),
            'sender': os.getenv('MAIL_DEFAULT_SENDER', 'Not configured')
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
