from __future__ import annotations

import os
from datetime import datetime

import httpx
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models import User, db

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


def _normalize_phone(phone: str | None) -> str:
    """Normalize a phone number for Twilio.

    - Strips spaces/dashes/parentheses
    - If all digits and length==10, optionally prefixes AI_CALLING_DEFAULT_COUNTRY_CODE (e.g. +91)
    """
    raw = (phone or '').strip()
    if not raw:
        return ''

    cleaned = ''.join(ch for ch in raw if ch.isdigit() or ch == '+')

    # keep only the first '+' if any
    if cleaned.count('+') > 1:
        cleaned = '+' + cleaned.replace('+', '')

    digits = ''.join(ch for ch in cleaned if ch.isdigit())
    if cleaned.startswith('+'):
        # E.164-ish; basic sanity
        if 10 <= len(digits) <= 15:
            return cleaned
        return ''

    default_cc = os.getenv('AI_CALLING_DEFAULT_COUNTRY_CODE', '').strip()
    if default_cc and len(digits) == 10:
        if not default_cc.startswith('+'):
            default_cc = '+' + default_cc
        return f'{default_cc}{digits}'

    # fallback: digits only
    if 10 <= len(digits) <= 15:
        return digits
    return ''


@ai_calling_bp.route('/health', methods=['GET'])
@jwt_required()
def ai_calling_health():
    """Return whether AI calling is configured/enabled."""
    enabled = _truthy(os.getenv('AI_CALLING_ENABLED'), default=False)
    service_url = os.getenv('AI_CALLING_SERVICE_URL', '').strip()
    endpoint = os.getenv('AI_CALLING_ENDPOINT', '/call').strip() or '/call'

    # When service_url is empty, the calling server is expected to be self-hosted
    # in the same Railway backend (ASGI via uvicorn).
    self_hosted = enabled and not service_url

    missing = []
    if enabled:
        # For self-hosted mode, we require Twilio + AI keys.
        if self_hosted:
            for k in ('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_FROM_NUMBER', 'CALLING_PUBLIC_URL'):
                if not (os.getenv(k) or '').strip():
                    missing.append(k)
            # AI voice pipeline
            if not (os.getenv('GROQ_API_KEY') or '').strip():
                missing.append('GROQ_API_KEY')
            if not (os.getenv('OPENAI_API_KEY') or '').strip():
                missing.append('OPENAI_API_KEY')

    configured = enabled and (bool(service_url) or self_hosted) and not missing

    return jsonify({
        'success': True,
        'enabled': enabled,
        'service_url_configured': bool(service_url),
        'self_hosted': self_hosted,
        'configured': configured,
        'endpoint': endpoint,
        'require_verified': _truthy(os.getenv('AI_CALLING_REQUIRE_VERIFIED'), default=True),
        'missing': missing,
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

        data = request.get_json(silent=True) or {}
        topic = (data.get('topic') or '').strip()
        notes = (data.get('notes') or '').strip()

        # Optional overrides (useful when phone/name is missing in profile)
        override_name = (data.get('name') or '').strip()
        override_phone = _normalize_phone(data.get('phone'))

        db_changed = False

        if override_name and not student.full_name:
            try:
                student.full_name = override_name
                db_changed = True
            except Exception:
                pass

        if override_phone and not phone:
            try:
                student.phone = override_phone
                db_changed = True
            except Exception:
                pass

        # Choose the phone used for the call.
        phone_for_call = override_phone or _normalize_phone(phone) or phone
        if not phone_for_call:
            return jsonify({'success': False, 'error': 'Phone number missing/invalid. Enter a valid mobile number (prefer +<countrycode><number>).'}), 400

        name_for_call = override_name or (student.full_name or '').strip()

        service_url = os.getenv('AI_CALLING_SERVICE_URL', '').strip().rstrip('/')
        self_hosted = not service_url

        endpoint = (os.getenv('AI_CALLING_ENDPOINT', '/call').strip() or '/call')
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint

        token = os.getenv('AI_CALLING_SERVICE_TOKEN', '').strip()
        timeout_s = float(os.getenv('AI_CALLING_TIMEOUT', '20'))

        payload = {
            'phone': phone_for_call,
            'name': name_for_call,
            'email': user.email,
            'topic': topic,
            'notes': notes,
            'requested_at': datetime.utcnow().isoformat() + 'Z',
            'source': 'placement-portal',
        }

        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        if self_hosted:
            # Avoid HTTP self-calls (can time out behind proxies).
            # For reliability and debuggability, initiate Twilio call synchronously
            # so we can return call_sid or a clear Twilio error.

            missing = [k for k in (
                'TWILIO_ACCOUNT_SID',
                'TWILIO_AUTH_TOKEN',
                'TWILIO_FROM_NUMBER',
                'CALLING_PUBLIC_URL',
            ) if not (os.getenv(k) or '').strip()]
            if missing:
                return jsonify({
                    'success': False,
                    'error': 'AI calling is not configured on the server (missing Twilio env vars)',
                    'missing': missing,
                }), 500

            # Best-effort persist overrides (don't fail call if DB write fails)
            if db_changed:
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()

            try:
                from ai_calling_twilio import initiate_twilio_call

                result = initiate_twilio_call(phone_for_call)
                return jsonify({
                    'success': True,
                    'message': 'Call initiated',
                    'calling_service_status': 200,
                    'calling_service_response': result,
                }), 200
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to initiate call: {str(e)}',
                }), 502

        url = f'{service_url}{endpoint}'
        timeout = httpx.Timeout(timeout_s, connect=min(5.0, timeout_s))
        with httpx.Client(timeout=timeout) as client:
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

    except httpx.TimeoutException:
        return jsonify({'success': False, 'error': 'Calling service timed out. Please try again.'}), 504
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
