import os
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, User, Application, HiringRound, StudentCalendarEvent
from google_calendar_service import calendar_configured, create_event, delete_event


calendar_bp = Blueprint('calendar', __name__, url_prefix='/api/student/calendar')


def _require_student(user_id: int):
    user = User.query.get(user_id)
    if not user or user.role_id != 1 or not user.student:
        return None
    return user.student


@calendar_bp.route('/health', methods=['GET'])
@jwt_required()
def calendar_health():
    """Returns whether Calendar API integration is configured."""
    return jsonify({
        'enabled': calendar_configured(),
        'calendar_id': os.getenv('GOOGLE_CALENDAR_ID') if calendar_configured() else None,
    }), 200


@calendar_bp.route('/events', methods=['GET'])
@jwt_required()
def list_events():
    user_id = int(get_jwt_identity())
    student = _require_student(user_id)
    if not student:
        return jsonify({'error': 'Unauthorized'}), 403

    events = StudentCalendarEvent.query.filter_by(student_id=student.id).order_by(StudentCalendarEvent.created_at.desc()).limit(200).all()
    return jsonify({
        'success': True,
        'events': [
            {
                'id': e.id,
                'application_id': e.application_id,
                'round_id': e.round_id,
                'calendar_id': e.calendar_id,
                'google_event_id': e.google_event_id,
                'html_link': e.html_link,
                'title': e.title,
                'location': e.location,
                'start_at': e.start_at.isoformat() if e.start_at else None,
                'end_at': e.end_at.isoformat() if e.end_at else None,
                'created_at': e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }), 200


@calendar_bp.route('/create-round', methods=['POST'])
@jwt_required()
def create_round_event():
    if not calendar_configured():
        return jsonify({'error': 'Google Calendar is not configured on server'}), 400

    user_id = int(get_jwt_identity())
    student = _require_student(user_id)
    if not student:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json(silent=True) or {}
    application_id = data.get('application_id')
    round_id = data.get('round_id')

    if not application_id or not round_id:
        return jsonify({'error': 'application_id and round_id are required'}), 400

    app = Application.query.get(int(application_id))
    if not app or app.student_id != student.id:
        return jsonify({'error': 'Application not found'}), 404

    hr = HiringRound.query.get(int(round_id))
    if not hr or hr.job_id != app.job_id:
        return jsonify({'error': 'Hiring round not found'}), 404

    if not hr.scheduled_date:
        return jsonify({'error': 'Round has no scheduled date'}), 400

    # Deduplicate: if already created for this student+round, return it
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
    existing = StudentCalendarEvent.query.filter_by(student_id=student.id, round_id=hr.id, calendar_id=calendar_id).first()
    if existing and existing.html_link:
        return jsonify({'success': True, 'html_link': existing.html_link, 'event_id': existing.google_event_id, 'existing': True}), 200

    start_dt = datetime.combine(hr.scheduled_date, hr.scheduled_time) if hr.scheduled_time else datetime.combine(hr.scheduled_date, datetime.min.time())
    if hr.scheduled_time:
        end_dt = start_dt + timedelta(minutes=60)
        all_day = False
    else:
        end_dt = start_dt + timedelta(days=1)
        all_day = True

    title = f"{app.job.company.company_name if app.job and app.job.company else 'Company'}: {app.job.title if app.job else 'Job'} — {hr.round_name}"
    details = f"Application #{app.id}\nRound: {hr.round_name}\nStatus: {app.status}"

    created = create_event(
        calendar_id=calendar_id,
        summary=title,
        description=details,
        location=hr.venue,
        start_dt=start_dt,
        end_dt=end_dt,
        all_day=all_day,
    )

    if not created:
        return jsonify({'error': 'Failed to create calendar event'}), 500

    db_event = StudentCalendarEvent(
        student_id=student.id,
        application_id=app.id,
        round_id=hr.id,
        calendar_id=calendar_id,
        google_event_id=created.get('id'),
        html_link=created.get('htmlLink'),
        title=title,
        location=hr.venue,
        start_at=start_dt,
        end_at=end_dt,
    )
    db.session.add(db_event)
    db.session.commit()

    return jsonify({'success': True, 'html_link': db_event.html_link, 'event_id': db_event.google_event_id}), 201


@calendar_bp.route('/create-interview', methods=['POST'])
@jwt_required()
def create_interview_event():
    if not calendar_configured():
        return jsonify({'error': 'Google Calendar is not configured on server'}), 400

    user_id = int(get_jwt_identity())
    student = _require_student(user_id)
    if not student:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json(silent=True) or {}
    application_id = data.get('application_id')

    if not application_id:
        return jsonify({'error': 'application_id is required'}), 400

    app = Application.query.get(int(application_id))
    if not app or app.student_id != student.id:
        return jsonify({'error': 'Application not found'}), 404

    if not getattr(app, 'interview_date', None):
        return jsonify({'error': 'Application has no interview_date'}), 400

    calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
    existing = StudentCalendarEvent.query.filter_by(student_id=student.id, application_id=app.id, round_id=None, calendar_id=calendar_id).first()
    if existing and existing.html_link:
        return jsonify({'success': True, 'html_link': existing.html_link, 'event_id': existing.google_event_id, 'existing': True}), 200

    start_dt = app.interview_date
    end_dt = start_dt + timedelta(minutes=60)

    title = f"{app.job.company.company_name if app.job and app.job.company else 'Company'}: {app.job.title if app.job else 'Job'} — Interview"
    details = f"Application #{app.id}\nInterview"

    created = create_event(
        calendar_id=calendar_id,
        summary=title,
        description=details,
        location=getattr(app, 'interview_location', None),
        start_dt=start_dt,
        end_dt=end_dt,
        all_day=False,
    )

    if not created:
        return jsonify({'error': 'Failed to create calendar event'}), 500

    db_event = StudentCalendarEvent(
        student_id=student.id,
        application_id=app.id,
        round_id=None,
        calendar_id=calendar_id,
        google_event_id=created.get('id'),
        html_link=created.get('htmlLink'),
        title=title,
        location=getattr(app, 'interview_location', None),
        start_at=start_dt,
        end_at=end_dt,
    )
    db.session.add(db_event)
    db.session.commit()

    return jsonify({'success': True, 'html_link': db_event.html_link, 'event_id': db_event.google_event_id}), 201


@calendar_bp.route('/events/<int:event_row_id>', methods=['DELETE'])
@jwt_required()
def remove_event(event_row_id: int):
    if not calendar_configured():
        return jsonify({'error': 'Google Calendar is not configured on server'}), 400

    user_id = int(get_jwt_identity())
    student = _require_student(user_id)
    if not student:
        return jsonify({'error': 'Unauthorized'}), 403

    ev = StudentCalendarEvent.query.get(event_row_id)
    if not ev or ev.student_id != student.id:
        return jsonify({'error': 'Event not found'}), 404

    ok = delete_event(calendar_id=ev.calendar_id, event_id=ev.google_event_id)
    try:
        db.session.delete(ev)
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify({'success': True, 'deleted_from_google': ok}), 200
