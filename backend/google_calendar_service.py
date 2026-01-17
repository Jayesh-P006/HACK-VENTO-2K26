import json
import os
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    CALENDAR_AVAILABLE = True
except Exception:
    CALENDAR_AVAILABLE = False


CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']


def calendar_configured() -> bool:
    if not CALENDAR_AVAILABLE:
        return False

    has_creds = bool(
        os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        or os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )
    return has_creds and bool(os.getenv('GOOGLE_CALENDAR_ID'))


def _load_service_account_credentials(scopes):
    if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
        return service_account.Credentials.from_service_account_info(
            json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')),
            scopes=scopes,
        )

    cred_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if cred_path and Path(cred_path).exists():
        return service_account.Credentials.from_service_account_file(cred_path, scopes=scopes)

    return None


def get_calendar_service():
    if not calendar_configured():
        return None

    try:
        creds = _load_service_account_credentials(CALENDAR_SCOPES)
        if not creds:
            return None
        return build('calendar', 'v3', credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"Calendar client error: {e}")
        return None


def create_event(
    *,
    calendar_id: str,
    summary: str,
    description: str | None,
    location: str | None,
    start_dt,
    end_dt,
    all_day: bool = False,
):
    service = get_calendar_service()
    if not service:
        return None

    event_body = {
        'summary': summary,
        'description': description or '',
        'location': location or '',
    }

    if all_day:
        event_body['start'] = {'date': start_dt.date().isoformat()}
        event_body['end'] = {'date': end_dt.date().isoformat()}
    else:
        # Use ISO strings with timezone if present, otherwise treat as local.
        event_body['start'] = {'dateTime': start_dt.isoformat()}
        event_body['end'] = {'dateTime': end_dt.isoformat()}

    try:
        created = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        return created
    except Exception as e:
        print(f"Calendar create event failed: {e}")
        return None


def delete_event(*, calendar_id: str, event_id: str) -> bool:
    service = get_calendar_service()
    if not service:
        return False

    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return True
    except Exception as e:
        print(f"Calendar delete event failed: {e}")
        return False
