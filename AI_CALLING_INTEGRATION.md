# AI Calling Assistant Integration

This repo now includes a student-facing UI + backend API to request an AI phone call.

The portal integrates with the AI calling server (FastAPI) as an **external service** over HTTP.

## What was added

- Backend endpoint (JWT-protected):
  - `POST /api/ai-calling/request` (student-only)
  - `GET /api/ai-calling/health` (student-only; shows configured/enabled)

- Student UI section:
  - New nav item **📞 AI Calling** in the student dashboard.
  - Form to request a call with optional topic/notes.

## How the backend triggers a call

The portal backend calls your AI calling server like this:

The portal backend calls your FastAPI server:

- URL: `${AI_CALLING_SERVICE_URL}${AI_CALLING_ENDPOINT}` (default `/call`)
- Method: `POST`
- JSON payload:

```json
{
  "phone": "<from student profile>",
  "name": "<from student profile>",
  "email": "<user email>",
  "topic": "<optional>",
  "notes": "<optional>",
  "requested_at": "2026-01-16T00:00:00Z",
  "source": "placement-portal"
}
```

If you want a different path/payload, update your calling server OR adjust `backend/ai_calling_routes.py`.

Separately, Twilio must be able to reach the FastAPI server's webhook:

- `POST /answer` returns TwiML that tells Twilio to connect to the WebSocket stream.
- This requires a public HTTPS URL (typically via ngrok). The calling server uses `CALLING_PUBLIC_URL` for this.

## Required environment variables (Railway backend)

Set these on Railway → Backend Service → Variables:

- `AI_CALLING_ENABLED=true`
- `AI_CALLING_SERVICE_URL=https://<your-calling-service-host>`
- `AI_CALLING_ENDPOINT=/call` (or whatever your server exposes)
- Optional:
  - `AI_CALLING_SERVICE_TOKEN=...` (sent as `Authorization: Bearer ...`)
  - `AI_CALLING_TIMEOUT=20`
  - `AI_CALLING_REQUIRE_VERIFIED=true` (default true)

## Local development

1. Start backend:
   - `start_backend.ps1`
2. Start your AI calling server:
  - Install dependencies: `pip install -r "AI CALLING/requierement.txt.txt"`
  - Set env vars from `AI CALLING/.env.example`
  - Run: `uvicorn server:app --host 0.0.0.0 --port 8000`
  - Run ngrok: `ngrok http 8000` and set `CALLING_PUBLIC_URL` to the generated HTTPS URL
3. Set backend env vars locally (example):

```dotenv
AI_CALLING_ENABLED=true
AI_CALLING_SERVICE_URL=http://localhost:8000
AI_CALLING_ENDPOINT=/call

## Security note

Never commit API keys (Twilio/Groq) into git. If you previously had keys in code, rotate them immediately.
```

## Notes / Safety

- The portal uses the **student’s phone from DB**. If it’s empty, the request is rejected.
- By default, `AI_CALLING_REQUIRE_VERIFIED=true` blocks unverified (OTP-not-verified) users.
