import json
import os
import re
from io import BytesIO
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    DRIVE_AVAILABLE = True
except Exception:
    DRIVE_AVAILABLE = False


DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']


def drive_configured() -> bool:
    if not DRIVE_AVAILABLE:
        return False
    return bool(
        os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        or os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
        or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    )


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


def get_drive_service():
    if not drive_configured():
        return None

    try:
        creds = _load_service_account_credentials(DRIVE_SCOPES)
        if not creds:
            return None
        return build('drive', 'v3', credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"Drive client error: {e}")
        return None


def upload_file(file_bytes: bytes, filename: str, mime_type: str | None = None, folder_id: str | None = None):
    service = get_drive_service()
    if not service:
        return None

    try:
        media = MediaIoBaseUpload(BytesIO(file_bytes), mimetype=mime_type or 'application/pdf', resumable=False)
        metadata = {'name': filename}
        if folder_id:
            metadata['parents'] = [folder_id]

        drive_file = service.files().create(
            body=metadata,
            media_body=media,
            fields='id, name, mimeType, webViewLink, webContentLink',
        ).execute()

        # Best-effort: make publicly readable so resume_url can be opened directly.
        # If this fails (org policy), UI should use backend download endpoint.
        try:
            service.permissions().create(
                fileId=drive_file['id'],
                body={'role': 'reader', 'type': 'anyone'},
            ).execute()
        except Exception as share_error:
            print(f"Drive share warning: {share_error}")

        return drive_file
    except Exception as e:
        print(f"Drive upload failed: {e}")
        return None


def download_file(file_id: str):
    service = get_drive_service()
    if not service:
        return None

    try:
        request = service.files().get_media(fileId=file_id)
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()
    except Exception as e:
        print(f"Drive download failed: {e}")
        return None


def delete_file(file_id: str) -> bool:
    service = get_drive_service()
    if not service:
        return False

    try:
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print(f"Drive delete failed: {e}")
        return False


def extract_file_id(value: str | None):
    if not value:
        return None

    if re.fullmatch(r'[A-Za-z0-9_-]{10,}', value):
        return value

    patterns = [r'/d/([^/]+)', r'id=([A-Za-z0-9_-]+)']
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    return None
