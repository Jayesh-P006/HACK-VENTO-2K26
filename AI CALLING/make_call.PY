from twilio.rest import Client

import os

ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '').strip()
FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', '').strip()
CALLING_PUBLIC_URL = os.getenv('CALLING_PUBLIC_URL', '').strip().rstrip('/')

if not ACCOUNT_SID or not AUTH_TOKEN or not FROM_NUMBER or not CALLING_PUBLIC_URL:
    raise SystemExit('Missing env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, CALLING_PUBLIC_URL')

client = Client(ACCOUNT_SID, AUTH_TOKEN)

to_number = os.getenv('CALL_TO_NUMBER', '').strip()
if not to_number:
    raise SystemExit('Set CALL_TO_NUMBER to the destination phone number, e.g. +91xxxxxxxxxx')

call = client.calls.create(
    to=to_number,
    from_=FROM_NUMBER,
    url=f"{CALLING_PUBLIC_URL}/answer",
)

print("Call SID:", call.sid)
