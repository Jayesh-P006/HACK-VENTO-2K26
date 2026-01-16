"""AI Calling server (FastAPI) integrated into the backend deployment.

This module exposes the Twilio webhook + WebSocket endpoints required for Twilio
Media Streams:
  - POST /answer   -> returns TwiML to connect to the WebSocket stream
  - WS   /media    -> handles Twilio Media Streams
  - POST /call     -> (optional) triggers call via Twilio REST

It is designed to be registered on an ASGI app (see asgi_app.py).
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor

import audioop
import numpy as np
import soundfile as sf
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import PlainTextResponse
from openai import OpenAI
from twilio.rest import Client

# NOTE: whisper is heavy; we load lazily to reduce cold-start time.


SAMPLE_RATE = 8000
FRAME_SIZE = 160  # 20ms μ-law frame
SILENCE_THRESHOLD = 350
BARGE_IN_THRESHOLD = 900

_executor = ThreadPoolExecutor(max_workers=3)
_stt_model = None
_groq_client = None


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "y", "on")


def _get_groq_client() -> OpenAI:
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    api_key = (os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key") or "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required for AI Calling")

    _groq_client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
    return _groq_client


def _get_whisper_model():
    global _stt_model
    if _stt_model is not None:
        return _stt_model

    try:
        import whisper  # provided by whisper-openai
    except Exception as e:
        raise RuntimeError(
            "Whisper STT is not available. Install 'whisper-openai' and its dependencies. "
            f"Original error: {e}"
        )

    model_name = os.getenv("AI_CALLING_WHISPER_MODEL", "tiny").strip() or "tiny"
    _stt_model = whisper.load_model(model_name)
    return _stt_model


def fetch_existing_readiness() -> dict:
    # TODO: replace with real DB-driven readiness once available.
    return {
        "score": 62,
        "decision": "APPLY WITH CAUTION",
        "skill_gaps": ["DSA", "System Design"],
        "strengths": ["Python", "SQL", "Projects"],
        "confidence": "MEDIUM",
    }


def is_placement_query(text: str) -> bool:
    keywords = [
        "ready",
        "readiness",
        "score",
        "placement",
        "interview",
        "skill",
        "gap",
        "strength",
        "weak",
        "improve",
        "prepare",
        "dsa",
        "system design",
        "coding",
        "resume",
        "job",
        "career",
        "company",
        "hiring",
        "internship",
        "apply",
    ]
    t = (text or "").lower()
    return any(kw in t for kw in keywords)


def is_goodbye(text: str) -> bool:
    goodbye_phrases = [
        "bye",
        "goodbye",
        "good bye",
        "bye bye",
        "thank you",
        "thanks",
        "thank u",
        "thanku",
        "thnx",
        "thanks for your help",
        "thank you for your help",
        "thanks for your guidance",
        "thank you for your guidance",
        "end call",
        "hang up",
        "disconnect",
        "cut the call",
        "that's all",
        "that is all",
        "nothing else",
        "no more questions",
        "i'm done",
        "i am done",
        "that's it",
        "that is it",
        "all done",
        "finished",
        "ok bye",
        "okay bye",
    ]
    tl = (text or "").lower().strip()
    return any(phrase in tl for phrase in goodbye_phrases)


def groq_reply(user_text: str, readiness: dict | None = None) -> str:
    if is_goodbye(user_text):
        return (
            "Thank you for connecting with Silent Syntax! "
            "Best of luck with your placements. Goodbye!"
        )

    if not is_placement_query(user_text):
        return (
            "I specialize in placement readiness guidance. "
            "Ask me about your readiness score, skill gaps, strengths, or improvement strategies."
        )

    system_prompt = (
        "You are Silent Syntax's placement readiness AI assistant on a phone call.\n"
        "Rules:\n"
        "1. Answer in 2 sentences maximum\n"
        "2. Be direct, clear, helpful\n"
        "3. Only discuss placement readiness\n"
        "4. Never guarantee placement\n"
        "5. NO follow-up questions\n"
    )

    if readiness:
        system_prompt += (
            f"\nStudent data: Score {readiness['score']}/100, "
            f"Gaps: {', '.join(readiness['skill_gaps'])}, "
            f"Strengths: {', '.join(readiness['strengths'])}"
        )

    client = _get_groq_client()
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        max_tokens=80,
        temperature=0.4,
    )

    reply = (response.choices[0].message.content or "").strip()
    for phrase in ["How can I", "What else", "Anything more", "Is there", "Let me know"]:
        if phrase in reply:
            reply = reply.split(phrase)[0].strip().rstrip(",") + "."
    return reply


def resample_to_8k(audio: np.ndarray, sr: int) -> np.ndarray:
    return audio if sr == 8000 else audio[:: max(1, sr // 8000)]


def detect_silence(chunk: np.ndarray, threshold: int = SILENCE_THRESHOLD) -> bool:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2))) < threshold


def detect_barge_in(chunk: np.ndarray, threshold: int = BARGE_IN_THRESHOLD) -> bool:
    return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2))) > threshold


async def tts_to_ulaw(text: str) -> bytes:
    try:
        import edge_tts
    except Exception as e:
        raise RuntimeError(
            "edge-tts is required for AI voice output. Install 'edge-tts'. "
            f"Original error: {e}"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        path = f.name

    await edge_tts.Communicate(
        text,
        voice=os.getenv("AI_CALLING_TTS_VOICE", "en-IN-NeerjaNeural"),
        rate=os.getenv("AI_CALLING_TTS_RATE", "+8%"),
    ).save(path)

    audio, sr = sf.read(path, dtype="int16")
    try:
        os.remove(path)
    except Exception:
        pass

    if getattr(audio, "ndim", 1) > 1:
        audio = audio[:, 0]

    audio_8k = resample_to_8k(audio, sr)
    return audioop.lin2ulaw(audio_8k.tobytes(), 2)


def transcribe(audio: np.ndarray) -> str:
    model = _get_whisper_model()

    audio_f32 = np.repeat(audio, 2).astype(np.float32) / 32768.0

    result = model.transcribe(
        audio_f32,
        language=os.getenv("AI_CALLING_STT_LANGUAGE", "en"),
        fp16=False,
        condition_on_previous_text=False,
        temperature=0.0,
        no_speech_threshold=0.5,
        compression_ratio_threshold=2.0,
    )
    return (result.get("text") or "").strip()


def _public_base_url_from_request(request: Request) -> str:
    configured = os.getenv("CALLING_PUBLIC_URL", "").strip().rstrip("/")
    if configured:
        return configured

    # Fallback: infer from forwarded headers
    scheme = request.headers.get("x-forwarded-proto") or "https"
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        return ""
    return f"{scheme}://{host}".rstrip("/")


def register_ai_calling_routes(app: FastAPI) -> None:
    @app.post("/answer")
    async def answer(request: Request):
        public_url = _public_base_url_from_request(request)
        if not public_url:
            raise HTTPException(status_code=500, detail="Cannot determine public URL for Twilio")

        ws_url = public_url.replace("https://", "wss://").replace("http://", "ws://") + "/media"

        return PlainTextResponse(
            f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Response>
    <Say voice=\"alice\">Hello! Connecting you to Silent Syntax placement assistant.</Say>
    <Connect>
        <Stream url=\"{ws_url}\" />
    </Connect>
    <Pause length=\"60\"/>
</Response>""",
            media_type="application/xml",
        )

    @app.post("/call")
    async def trigger_call(request: Request):
        data = await request.json()
        to_phone = (data.get("phone") or "").strip()
        if not to_phone:
            raise HTTPException(status_code=400, detail="phone is required")

        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()
        public_url = (os.getenv("CALLING_PUBLIC_URL", "").strip() or _public_base_url_from_request(request)).rstrip("/")
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
            raise HTTPException(status_code=500, detail=f"Missing env vars: {', '.join(missing)}")

        webhook_url = f"{public_url}{webhook_path}"

        try:
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
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Twilio call failed: {str(e)}")

    @app.websocket("/media")
    async def media(ws: WebSocket):
        await ws.accept()

        stream_sid = None
        audio_buf: list[np.ndarray] = []
        silence_chunks = 0
        speech_chunks = 0
        is_processing = False
        greeting_sent = False

        send_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        speaking = False

        async def sender():
            while True:
                frame = await send_queue.get()
                if frame is None:
                    return
                await ws.send_json(
                    {
                        "event": "media",
                        "streamSid": stream_sid,
                        "media": {"payload": base64.b64encode(frame).decode()},
                    }
                )
                await asyncio.sleep(0.02)

        sender_task = asyncio.create_task(sender())

        async def speak(text: str):
            nonlocal speaking
            speaking = True
            ulaw = await tts_to_ulaw(text)
            for i in range(0, len(ulaw), FRAME_SIZE):
                if not speaking:
                    break
                await send_queue.put(ulaw[i : i + FRAME_SIZE])
            speaking = False

        try:
            async for msg in ws.iter_text():
                data = json.loads(msg)
                event = data.get("event")

                if event == "start":
                    stream_sid = data["start"]["streamSid"]
                    if not greeting_sent:
                        greeting = (
                            "Hello! I'm your Silent Syntax placement readiness assistant. "
                            "I can help you understand your readiness score, identify skill gaps, "
                            "highlight your strengths, and suggest improvement strategies. "
                            "What would you like to know?"
                        )
                        await speak(greeting)
                        greeting_sent = True

                elif event == "media":
                    pcm = audioop.ulaw2lin(base64.b64decode(data["media"]["payload"]), 2)
                    chunk = np.frombuffer(pcm, dtype=np.int16)

                    if speaking and detect_barge_in(chunk):
                        speaking = False
                        audio_buf.clear()
                        silence_chunks = 0
                        speech_chunks = 0
                        continue

                    if speaking or is_processing:
                        continue

                    audio_buf.append(chunk)

                    if detect_silence(chunk):
                        silence_chunks += 1
                    else:
                        speech_chunks += 1
                        silence_chunks = 0

                    if speech_chunks > 10 and silence_chunks >= 35:
                        is_processing = True

                        audio = np.concatenate(audio_buf)
                        audio_buf.clear()
                        silence_chunks = 0
                        speech_chunks = 0

                        if len(audio) < 3000:
                            is_processing = False
                            continue

                        transcript = await asyncio.get_event_loop().run_in_executor(
                            _executor,
                            transcribe,
                            audio,
                        )

                        if transcript and len(transcript) > 1:
                            if is_goodbye(transcript):
                                readiness = fetch_existing_readiness()
                                goodbye_msg = groq_reply(transcript, readiness)
                                await speak(goodbye_msg)
                                await asyncio.sleep(2)
                                break

                            readiness = fetch_existing_readiness() if is_placement_query(transcript) else None
                            ai_response = groq_reply(transcript, readiness)
                            await speak(ai_response)

                        is_processing = False

                elif event == "stop":
                    break

        finally:
            await send_queue.put(None)
            await sender_task
            await ws.close()
