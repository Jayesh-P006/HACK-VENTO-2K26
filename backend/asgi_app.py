import os

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
# To reduce cold-start time, we register a lightweight stub first and lazy-load
# the full AI calling server only when those endpoints are actually hit.
if _truthy(os.getenv("AI_CALLING_ENABLED"), default=False):

    @app.on_event("startup")
    async def _register_ai_calling_lazy():
        # Nothing to do at startup; endpoints below lazy-load on first call.
        return

    _ai_routes_loaded = {"loaded": False}

    def _ensure_ai_calling_routes_loaded():
        if _ai_routes_loaded["loaded"]:
            return
        from ai_calling_server import register_ai_calling_routes

        register_ai_calling_routes(app)
        _ai_routes_loaded["loaded"] = True

    @app.api_route("/answer", methods=["POST"])
    async def _answer_lazy(request):
        _ensure_ai_calling_routes_loaded()
        # After registering, FastAPI will route to the real handler.
        # We re-dispatch by calling the app as an ASGI callable via Starlette.
        from starlette.requests import Request
        from starlette.responses import Response
        scope = request.scope
        req = Request(scope, request.receive)
        # Find the now-registered endpoint function
        for route in app.router.routes:
            if getattr(route, "path", None) == "/answer" and "POST" in getattr(route, "methods", set()) and route.endpoint != _answer_lazy:
                return await route.endpoint(req)
        return Response("AI calling route not available", status_code=503)

    @app.api_route("/call", methods=["POST"])
    async def _call_lazy(request):
        _ensure_ai_calling_routes_loaded()
        from starlette.requests import Request
        from starlette.responses import Response
        scope = request.scope
        req = Request(scope, request.receive)
        for route in app.router.routes:
            if getattr(route, "path", None) == "/call" and "POST" in getattr(route, "methods", set()) and route.endpoint != _call_lazy:
                return await route.endpoint(req)
        return Response("AI calling route not available", status_code=503)

    @app.websocket("/media")
    async def _media_lazy(ws):
        _ensure_ai_calling_routes_loaded()
        # Find and call the registered websocket handler
        for route in app.router.routes:
            if getattr(route, "path", None) == "/media" and getattr(route, "endpoint", None) != _media_lazy:
                return await route.endpoint(ws)
        await ws.close(code=1013)

# Mount the existing Flask app last so it acts as a fallback for all other routes
# (e.g. /api/*, /portal/*, etc.).
app.mount("/", WSGIMiddleware(flask_app))
