"""
ENHANCED AI CALLING AGENT - OPTIMIZED VERSION
✅ Smart call hangup detection
✅ Professional introduction
✅ Reduced latency (faster responses)
✅ Barge-in feature
"""

import base64, json, audioop, numpy as np, whisper, edge_tts, tempfile, os, asyncio
from fastapi import FastAPI, WebSocket, Request
from fastapi import HTTPException
from fastapi.responses import PlainTextResponse
from openai import OpenAI
import soundfile as sf
from concurrent.futures import ThreadPoolExecutor
from twilio.rest import Client

app = FastAPI()

# ================= CONFIG =================
SAMPLE_RATE = 8000
FRAME_SIZE = 160  # 20ms μ-law frame
SILENCE_THRESHOLD = 350  # Lower = more sensitive (faster response)
BARGE_IN_THRESHOLD = 900

executor = ThreadPoolExecutor(max_workers=3)  # Increased for parallel processing

GROQ_API_KEY = os.getenv('GROQ_API_KEY') or os.getenv('GROQ_API_KEY'.lower())
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
if not GROQ_API_KEY:
    raise RuntimeError('GROQ_API_KEY is required (set as env var)')

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

print("✅ Groq client initialized")
print("🧠 Loading Whisper...")
stt_model = whisper.load_model("base")
print("✅ Whisper loaded")

# ================= PLACEMENT READINESS DATA =================

def fetch_existing_readiness():
    """Get student's placement readiness data"""
    return {
        "score": 62,
        "decision": "APPLY WITH CAUTION",
        "skill_gaps": ["DSA", "System Design"],
        "strengths": ["Python", "SQL", "Projects"],
        "confidence": "MEDIUM"
    }

# ================= QUERY CLASSIFICATION =================

def is_placement_query(text: str) -> bool:
    """Check if query is about placement readiness"""
    keywords = [
        "ready", "readiness", "score", "placement", "interview",
        "skill", "gap", "strength", "weak", "improve", "prepare",
        "dsa", "system design", "coding", "resume", "job", "career",
        "company", "hiring", "internship", "apply"
    ]
    return any(kw in text.lower() for kw in keywords)

def is_goodbye(text: str) -> bool:
    """
    Enhanced goodbye detection - recognizes many ways to end call
    """
    goodbye_phrases = [
        # Direct goodbyes
        "bye", "goodbye", "good bye", "bye bye",
        
        # Thank you variations
        "thank you", "thanks", "thank u", "thanku", "thnx",
        "thanks for your help", "thank you for your help",
        "thanks for your guidance", "thank you for your guidance",
        "thanks for the information", "thank you for the information",
        
        # End call phrases
        "end call", "hang up", "disconnect", "cut the call",
        "that's all", "that is all", "nothing else", "no more questions",
        
        # Closing phrases
        "i'm done", "i am done", "that's it", "that is it",
        "all done", "finished", "ok bye", "okay bye"
    ]
    
    text_lower = text.lower().strip()
    return any(phrase in text_lower for phrase in goodbye_phrases)

# ================= GROQ AI RESPONSE =================

def groq_reply(user_text: str, readiness=None) -> str:
    """Generate AI response using Groq - optimized for speed"""
    
    # Handle goodbye with appreciation
    if is_goodbye(user_text):
        return (
            "Thank you for connecting with Silent Syntax! "
            "Best of luck with your placements. Goodbye!"
        )
    
    # Handle off-topic
    if not is_placement_query(user_text):
        return (
            "I specialize in placement readiness guidance. "
            "Ask me about your readiness score, skill gaps, strengths, or improvement strategies."
        )
    
    # Construct system prompt (concise for speed)
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

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            max_tokens=80,  # Reduced for faster response
            temperature=0.4,
        )
        
        reply = response.choices[0].message.content.strip()
        
        # Remove chatty phrases
        for phrase in ["How can I", "What else", "Anything more", "Is there", "Let me know"]:
            if phrase in reply:
                reply = reply.split(phrase)[0].strip().rstrip(',') + '.'
        
        return reply
        
    except Exception as e:
        print(f"❌ Groq error: {e}")
        if readiness:
            return f"Your readiness score is {readiness['score']} with gaps in {' and '.join(readiness['skill_gaps'])}."
        return "I'm here to help with placement readiness. What would you like to know?"

# ================= AUDIO PROCESSING =================

def resample_to_8k(audio, sr):
    """Downsample to 8kHz for Twilio"""
    return audio if sr == 8000 else audio[:: max(1, sr // 8000)]

def detect_silence(chunk, threshold=SILENCE_THRESHOLD):
    """Detect if audio chunk is silence"""
    return np.sqrt(np.mean(chunk.astype(np.float32) ** 2)) < threshold

def detect_barge_in(chunk, threshold=BARGE_IN_THRESHOLD):
    """Detect if user is trying to interrupt"""
    return np.sqrt(np.mean(chunk.astype(np.float32) ** 2)) > threshold

# ================= TEXT-TO-SPEECH (OPTIMIZED) =================

async def tts_to_ulaw(text: str) -> bytes:
    """Generate TTS - optimized for speed"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        path = f.name
    
    await edge_tts.Communicate(
        text, 
        voice="en-IN-NeerjaNeural",
        rate="+8%"  # Slightly faster for reduced latency
    ).save(path)
    
    audio, sr = sf.read(path, dtype="int16")
    os.remove(path)
    
    if audio.ndim > 1:
        audio = audio[:, 0]
    
    audio_8k = resample_to_8k(audio, sr)
    return audioop.lin2ulaw(audio_8k.tobytes(), 2)

# ================= SPEECH-TO-TEXT (OPTIMIZED) =================

def transcribe(audio):
    """Transcribe audio using Whisper - optimized settings"""
    try:
        # Upsample to 16kHz for Whisper
        audio = np.repeat(audio, 2).astype(np.float32) / 32768.0
        
        result = stt_model.transcribe(
            audio, 
            language="en", 
            fp16=False,
            condition_on_previous_text=False,
            temperature=0.0,
            no_speech_threshold=0.5,  # Skip faster if no speech
            compression_ratio_threshold=2.0  # Faster processing
        )
        
        return result["text"].strip()
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return ""

# ================= TWILIO WEBHOOK =================

@app.post("/answer")
async def answer(request: Request):
    """Twilio webhook - returns TwiML to connect to WebSocket"""
    host = request.headers.get("host")
    print(f"📞 Call received - connecting to wss://{host}/media")
    
    return PlainTextResponse(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="wss://{host}/media"/>
    </Connect>
    <Pause length="60"/>
</Response>""",
        media_type="application/xml"
    )


@app.post('/call')
async def trigger_call(request: Request):
    """Trigger a phone call via Twilio.

    Expects JSON: {"phone":"+91..."}

    Required env vars:
      - TWILIO_ACCOUNT_SID
      - TWILIO_AUTH_TOKEN
      - TWILIO_FROM_NUMBER
      - CALLING_PUBLIC_URL  (public https URL Twilio can reach, e.g. your ngrok URL)

    Optional:
      - TWILIO_WEBHOOK_PATH (default /answer)
    """
    data = await request.json()
    to_phone = (data.get('phone') or '').strip()
    if not to_phone:
        raise HTTPException(status_code=400, detail='phone is required')

    account_sid = os.getenv('TWILIO_ACCOUNT_SID', '').strip()
    auth_token = os.getenv('TWILIO_AUTH_TOKEN', '').strip()
    from_number = os.getenv('TWILIO_FROM_NUMBER', '').strip()
    public_url = os.getenv('CALLING_PUBLIC_URL', '').strip().rstrip('/')
    webhook_path = (os.getenv('TWILIO_WEBHOOK_PATH', '/answer').strip() or '/answer')
    if not webhook_path.startswith('/'):
        webhook_path = '/' + webhook_path

    missing = [k for k, v in [
        ('TWILIO_ACCOUNT_SID', account_sid),
        ('TWILIO_AUTH_TOKEN', auth_token),
        ('TWILIO_FROM_NUMBER', from_number),
        ('CALLING_PUBLIC_URL', public_url),
    ] if not v]
    if missing:
        raise HTTPException(status_code=500, detail=f'Missing env vars: {", ".join(missing)}')

    webhook_url = f'{public_url}{webhook_path}'

    try:
        twilio_client = Client(account_sid, auth_token)
        call = twilio_client.calls.create(
            to=to_phone,
            from_=from_number,
            url=webhook_url,
        )
        return {
            'success': True,
            'message': 'Call initiated',
            'call_sid': call.sid,
            'to': to_phone,
            'from': from_number,
            'webhook_url': webhook_url,
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'Twilio call failed: {str(e)}')

# ================= WEBSOCKET MEDIA HANDLER =================

@app.websocket("/media")
async def media(ws: WebSocket):
    """
    Handle Twilio Media Streams
    Features: Barge-in, Smart hangup, Fast responses
    """
    await ws.accept()
    print("✅ WebSocket connected")

    stream_sid = None
    audio_buf = []
    silence_chunks = 0
    speech_chunks = 0
    is_processing = False
    greeting_sent = False

    # Queue for sending audio frames
    send_queue = asyncio.Queue()
    speaking = False

    async def sender():
        """Background task to send audio frames"""
        nonlocal speaking
        while True:
            frame = await send_queue.get()
            if frame is None:
                return
            await ws.send_json({
                "event": "media",
                "streamSid": stream_sid,
                "media": {"payload": base64.b64encode(frame).decode()}
            })
            await asyncio.sleep(0.02)

    sender_task = asyncio.create_task(sender())

    async def speak(text):
        """Send AI speech in frames (allows interruption)"""
        nonlocal speaking
        print(f"🤖 AI: {text}")
        speaking = True
        ulaw = await tts_to_ulaw(text)
        
        for i in range(0, len(ulaw), FRAME_SIZE):
            if not speaking:
                print("⚠️ Speech interrupted by user")
                break
            await send_queue.put(ulaw[i:i + FRAME_SIZE])
        
        speaking = False

    try:
        async for msg in ws.iter_text():
            data = json.loads(msg)
            event = data.get("event")

            if event == "start":
                stream_sid = data["start"]["streamSid"]
                print(f"📞 Stream started: {stream_sid}")
                
                # Professional introduction
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
                # Decode incoming audio
                pcm = audioop.ulaw2lin(base64.b64decode(data["media"]["payload"]), 2)
                chunk = np.frombuffer(pcm, dtype=np.int16)

                # Barge-in detection
                if speaking and detect_barge_in(chunk):
                    print("🛑 BARGE-IN - User interrupting")
                    speaking = False
                    audio_buf.clear()
                    silence_chunks = 0
                    speech_chunks = 0
                    continue

                # Don't buffer while AI speaks or processing
                if speaking or is_processing:
                    continue

                # Buffer user audio
                audio_buf.append(chunk)

                # Detect speech vs silence
                if detect_silence(chunk):
                    silence_chunks += 1
                else:
                    speech_chunks += 1
                    silence_chunks = 0

                # OPTIMIZED: Process after 0.7s silence (was 1.0s)
                # 35 chunks ≈ 0.7 seconds (faster response)
                if speech_chunks > 10 and silence_chunks >= 35:
                    is_processing = True
                    
                    # Combine audio
                    audio = np.concatenate(audio_buf)
                    audio_buf.clear()
                    silence_chunks = 0
                    speech_chunks = 0

                    # Skip very short audio
                    if len(audio) < 3000:  # 0.375s at 8kHz
                        is_processing = False
                        continue

                    print(f"🎙️ Processing ({len(audio)/8000:.2f}s)...")

                    # Transcribe in parallel
                    transcript = await asyncio.get_event_loop().run_in_executor(
                        executor, 
                        transcribe, 
                        audio
                    )

                    if transcript and len(transcript) > 1:
                        print(f"👤 USER: {transcript}")

                        # Check for hangup FIRST
                        if is_goodbye(transcript):
                            print("👋 Goodbye detected - ending call")
                            
                            # Get readiness for goodbye message
                            readiness = fetch_existing_readiness()
                            goodbye_msg = groq_reply(transcript, readiness)
                            
                            await speak(goodbye_msg)
                            await asyncio.sleep(2)
                            print("📞 Call ended")
                            break

                        # Get readiness data if placement query
                        readiness = None
                        if is_placement_query(transcript):
                            readiness = fetch_existing_readiness()

                        # Generate response (optimized)
                        ai_response = groq_reply(transcript, readiness)

                        # Speak response
                        await speak(ai_response)
                    else:
                        print("⚠️ Empty transcription")

                    is_processing = False

            elif event == "stop":
                print("📞 Stream stopped")
                break

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        await send_queue.put(None)
        await sender_task
        await ws.close()
        print("🔌 WebSocket closed")

# ================= HEALTH CHECK =================

@app.get("/")
async def health():
    return {
        "status": "ok",
        "service": "Silent Syntax AI Calling Agent",
        "features": ["barge-in", "smart-hangup", "fast-response"]
    }

# ================= RUN SERVER =================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 SILENT SYNTAX AI CALLING AGENT")
    print("="*60)
    print("✅ Smart call hangup")
    print("✅ Professional introduction")
    print("✅ Optimized for low latency")
    print("✅ Barge-in enabled")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)