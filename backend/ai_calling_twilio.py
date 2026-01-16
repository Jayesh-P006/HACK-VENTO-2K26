from __future__ import annotations

import os
from urllib.parse import urlsplit

from twilio.rest import Client


def initiate_twilio_call(to_phone: str) -> dict:
    """Initiate a Twilio outbound call to `to_phone`.

    Required env vars:
      - TWILIO_ACCOUNT_SID
      - TWILIO_AUTH_TOKEN
      - TWILIO_FROM_NUMBER
      - CALLING_PUBLIC_URL  (public https URL to this backend, e.g. https://<app>.up.railway.app)

    Optional:
      - TWILIO_WEBHOOK_PATH (default /answer)

    Returns a JSON-serializable dict.
    """
    to_phone = (to_phone or "").strip()
    if not to_phone:
        raise ValueError("phone is required")

    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    public_url = _canonical_public_url(os.getenv("CALLING_PUBLIC_URL", "").strip()).rstrip("/")
    webhook_path = (os.getenv("TWILIO_WEBHOOK_PATH", "/answer").strip() or "/answer")
    if not webhook_path.startswith("/"):
        webhook_path = "/" + webhook_path

    missing = [
        k
        for k, v in [
            ("TWILIO_ACCOUNT_SID", account_sid),
            ("TWILIO_AUTH_TOKEN", auth_token),
            ("TWILIO_FROM_NUMBER", from_number),
            ("CALLING_PUBLIC_URL", public_url),
        ]
        if not v
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    webhook_url = f"{public_url}{webhook_path}"
    status_url = f"{public_url}/twilio/status"

    twilio_client = Client(account_sid, auth_token)
    call = twilio_client.calls.create(
        to=to_phone,
        from_=from_number,
        url=webhook_url,
        status_callback=status_url,
        status_callback_method="POST",
        status_callback_event=["initiated", "ringing", "answered", "completed"],
    )

    return {
        "success": True,
        "message": "Call initiated",
        "call_sid": call.sid,
        "to": to_phone,
        "from": from_number,
        "webhook_url": webhook_url,
        "status_callback_url": status_url,
    }


def _canonical_public_url(raw_url: str) -> str:
    """Normalize a public URL to just scheme://host.

    This avoids misconfiguration like `https://<host>/api` which would cause
    Twilio to request a non-existent `/api/answer`.
    """
    raw = (raw_url or "").strip()
    if not raw:
        return ""

    if "://" not in raw:
        raw = f"https://{raw}"

    parts = urlsplit(raw)
    if not parts.netloc:
        return ""

    scheme = (parts.scheme or "https").lower()
    if scheme not in ("http", "https"):
        scheme = "https"

    return f"{scheme}://{parts.netloc}".rstrip("/")
