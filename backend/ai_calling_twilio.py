from __future__ import annotations

import os

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
    public_url = os.getenv("CALLING_PUBLIC_URL", "").strip().rstrip("/")
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

    twilio_client = Client(account_sid, auth_token)
    call = twilio_client.calls.create(
        to=to_phone,
        from_=from_number,
        url=webhook_url,
    )

    return {
        "success": True,
        "message": "Call initiated",
        "call_sid": call.sid,
        "to": to_phone,
        "from": from_number,
        "webhook_url": webhook_url,
    }
