# Railway-friendly Dockerfile for combined Flask (WSGI) + AI Calling (FastAPI/WebSocket)
# Runs uvicorn (ASGI) and mounts Flask via WSGIMiddleware.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps commonly needed by soundfile/whisper stacks
RUN apt-get update \
    ; apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    ; rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Railway provides $PORT at runtime
CMD ["sh", "-c", "uvicorn asgi_app:app --host 0.0.0.0 --port ${PORT:-8000}"]
