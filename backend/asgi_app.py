import os

print("[asgi] booting asgi_app...")

from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

# Import the existing Flask (WSGI) app.
# Note: importing `app` runs DB init/seed (idempotent) as implemented in app.py.
from app import app as flask_app


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "y", "on")


app = FastAPI(title="Silent Syntax Portal (ASGI)")

# Register AI Calling (FastAPI HTTP + WebSocket) routes on the ASGI app.
# These routes must be handled by an ASGI server (uvicorn), not gunicorn.
if _truthy(os.getenv("AI_CALLING_ENABLED"), default=False):
    from ai_calling_server import register_ai_calling_routes

    register_ai_calling_routes(app)
    print("[asgi] AI calling routes registered")
else:
    print("[asgi] AI calling disabled")

# Mount the existing Flask app last so it acts as a fallback for all other routes
# (e.g. /api/*, /portal/*, etc.).
app.mount("/", WSGIMiddleware(flask_app))
print("[asgi] mounted Flask app")
