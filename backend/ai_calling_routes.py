from __future__ import annotations

import os
from datetime import datetime

import httpx
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import User

ai_calling_bp = Blueprint('ai_calling', __name__, url_prefix='/api/ai-calling')


def _get_user_id() -> int:
    identity = get_jwt_identity()
    try:
        return int(identity)
    except Exception:
        raise ValueError('Invalid auth identity')


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')


@ai_calling_bp.route('/health', methods=['GET'])
@jwt_required()
def ai_calling_health():
    """Return whether AI calling is configured/enabled."""
    enabled = _truthy(os.getenv('AI_CALLING_ENABLED'), default=False)
    service_url = os.getenv('AI_CALLING_SERVICE_URL', '').strip()
    endpoint = os.getenv('AI_CALLING_ENDPOINT', '/call').strip() or '/call'

    return jsonify({
        'success': True,
        'enabled': enabled,
        'service_url_configured': bool(service_url),
        'endpoint': endpoint,
        'require_verified': _truthy(os.getenv('AI_CALLING_REQUIRE_VERIFIED'), default=True),
    }), 200


@ai_calling_bp.route('/request', methods=['POST'])
@jwt_required()
def request_ai_call():
    """Request an AI assistant call for the logged-in student.

    This endpoint:
    - Authenticates via JWT
    - Looks up the student's name/phone from DB
    - Calls an external calling service (your AI calling assistant server)

    Env vars (Railway/backend):
    - AI_CALLING_ENABLED=true
    - AI_CALLING_SERVICE_URL=http://<host>:<port>  (or https://...)
    - AI_CALLING_ENDPOINT=/call (optional)
    - AI_CALLING_SERVICE_TOKEN=... (optional)
    - AI_CALLING_REQUIRE_VERIFIED=true (default true)
    """
    try:
        if not _truthy(os.getenv('AI_CALLING_ENABLED'), default=False):
            return jsonify({
                'success': False,
                'error': 'AI calling is disabled on the server'
            }), 501

        user_id = _get_user_id()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        if user.role_id != 1:
            return jsonify({'success': False, 'error': 'Unauthorized - Student access only'}), 403

        if _truthy(os.getenv('AI_CALLING_REQUIRE_VERIFIED'), default=True) and not user.is_verified:
            return jsonify({'success': False, 'error': 'Email not verified. Please verify OTP first.'}), 403

        student = user.student
        if not student:
            return jsonify({'success': False, 'error': 'Student profile not found'}), 404

        phone = (student.phone or '').strip()
        if not phone:
            return jsonify({'success': False, 'error': 'Phone number missing in profile. Update your profile first.'}), 400

        data = request.get_json(silent=True) or {}
        topic = (data.get('topic') or '').strip()
        notes = (data.get('notes') or '').strip()

        service_url = os.getenv('AI_CALLING_SERVICE_URL', '').strip().rstrip('/')
        if not service_url:
            # Default to same-origin when AI calling server is embedded in this backend.
            scheme = request.headers.get('X-Forwarded-Proto', request.scheme) or 'https'
            host = request.headers.get('X-Forwarded-Host', request.host)
            service_url = f'{scheme}://{host}'.rstrip('/')

        endpoint = (os.getenv('AI_CALLING_ENDPOINT', '/call').strip() or '/call')
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint

        token = os.getenv('AI_CALLING_SERVICE_TOKEN', '').strip()
        timeout_s = float(os.getenv('AI_CALLING_TIMEOUT', '20'))

        payload = {
            'phone': phone,
            'name': student.full_name,
            'email': user.email,
            'topic': topic,
            'notes': notes,
            'requested_at': datetime.utcnow().isoformat() + 'Z',
            'source': 'placement-portal',
        }

        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        url = f'{service_url}{endpoint}'
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.post(url, json=payload, headers=headers)

        content_type = resp.headers.get('content-type', '')
        response_body = None
        if 'application/json' in content_type.lower():
            try:
                response_body = resp.json()
            except Exception:
                response_body = {'raw': resp.text}
        else:
            response_body = {'raw': resp.text}

        if resp.status_code >= 400:
            return jsonify({
                'success': False,
                'error': 'Calling service returned an error',
                'calling_service_status': resp.status_code,
                'calling_service_response': response_body,
            }), 502

        return jsonify({
            'success': True,
            'message': 'Call request submitted',
            'calling_service_status': resp.status_code,
            'calling_service_response': response_body,
        }), 200

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
