# M12 Advanced Voice Pipeline — Design Spec

> **Status:** Approved
> **Date:** 2026-03-16
> **Module:** M12 (V4 P0)

## Goal

Replace browser-only Web Speech API and Piper WASM TTS with a backend voice pipeline using LiteLLM Proxy. Backend STT (Gemini) + TTS (Vertex AI) with HTTP streaming. Existing browser solutions become fallbacks.

## Decisions

| Decision | Choice | Reason |
|---|---|---|
| STT provider | Gemini 2.0 Flash via LiteLLM (`gemini-stt`) | Already configured in proxy, free tier, good Vietnamese accuracy |
| TTS provider | Vertex AI Chirp3 HD via LiteLLM (`vertex-tts`) | Production-ready, high quality Vietnamese voice |
| TTS delivery | HTTP chunked streaming | Low latency (< 500ms first byte), simpler than WS multiplex |
| STT flow | Record audio blob → POST upload | Cross-platform (web + future Zalo Mini App), simple |
| Fallback | Keep Web Speech API (STT) + Piper WASM (TTS) | Code already exists, zero extra effort, resilient |

## Backend

### New files

```
backend/voice/__init__.py
backend/voice/stt.py       — transcribe(audio_bytes) -> str
backend/voice/tts.py        — speak(text, voice) -> AsyncGenerator[bytes]
backend/api/v1/voice.py    — FastAPI router
```

### API Endpoints

**POST /api/v1/voice/transcribe**
- Auth: Bearer token
- Input: `multipart/form-data`, field `audio` (webm/wav/mp3, max 10MB)
- Process: send audio to LiteLLM proxy model `gemini-stt` (OpenAI-compatible audio transcription)
- Output: `{ "text": "...", "language": "vi", "duration_ms": 1234 }`

**GET /api/v1/voice/speak?text=...&voice=vi-VN**
- Auth: Bearer token
- Input: query param `text` (max 2000 chars), optional `voice`
- Process: send text to LiteLLM proxy model `vertex-tts`, stream audio chunks
- Output: `StreamingResponse` with `content-type: audio/wav`, `Transfer-Encoding: chunked`

### voice/stt.py

```python
from openai import AsyncOpenAI
from core.config import settings

_client = AsyncOpenAI(api_key=settings.LITELLM_API_KEY, base_url=settings.LITELLM_BASE_URL)

async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """Transcribe audio via LiteLLM proxy (gemini-stt)."""
    transcript = await _client.audio.transcriptions.create(
        model="gemini-stt",
        file=(filename, audio_bytes),
        language="vi",
    )
    return {"text": transcript.text, "language": "vi"}
```

### voice/tts.py

```python
from openai import AsyncOpenAI
from core.config import settings

_client = AsyncOpenAI(api_key=settings.LITELLM_API_KEY, base_url=settings.LITELLM_BASE_URL)

async def speak(text: str, voice: str = "vi-VN") -> bytes:
    """Generate speech via LiteLLM proxy (vertex-tts). Returns audio bytes."""
    response = await _client.audio.speech.create(
        model="vertex-tts",
        input=text,
        voice=voice,
        response_format="wav",
    )
    return response.content

async def speak_stream(text: str, voice: str = "vi-VN"):
    """Stream speech chunks via LiteLLM proxy (vertex-tts)."""
    response = await _client.audio.speech.create(
        model="vertex-tts",
        input=text,
        voice=voice,
        response_format="wav",
    )
    # LiteLLM returns full response; yield in chunks for StreamingResponse
    content = response.content
    chunk_size = 8192
    for i in range(0, len(content), chunk_size):
        yield content[i:i + chunk_size]
```

### api/v1/voice.py

```python
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from core.deps import get_current_user_id
from core.config import settings
from voice.stt import transcribe
from voice.tts import speak_stream

router = APIRouter()

@router.post("/transcribe")
async def voice_transcribe(
    audio: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    if not settings.VOICE_ENABLED:
        raise HTTPException(503, "Voice is disabled")
    data = await audio.read()
    if len(data) > settings.VOICE_MAX_AUDIO_SIZE:
        raise HTTPException(413, "Audio too large (max 10MB)")
    result = await transcribe(data, audio.filename or "audio.webm")
    return result

@router.get("/speak")
async def voice_speak(
    text: str = Query(..., max_length=2000),
    voice: str = Query("vi-VN"),
    user_id: str = Depends(get_current_user_id),
):
    if not settings.VOICE_ENABLED:
        raise HTTPException(503, "Voice is disabled")
    return StreamingResponse(
        speak_stream(text, voice),
        media_type="audio/wav",
    )
```

### Config additions (core/config.py)

```python
VOICE_ENABLED: bool = True
VOICE_MAX_AUDIO_SIZE: int = 10 * 1024 * 1024  # 10MB
VOICE_TTS_MAX_CHARS: int = 2000
```

### Registration (main.py)

```python
from api.v1 import voice
app.include_router(voice.router, prefix=f"{_v1}/voice", tags=["voice"])
```

## Frontend

### useSTT (frontend/lib/hooks/use-voice.ts)

Rewrite to record audio blob via MediaRecorder API, POST to `/voice/transcribe`, fallback to Web Speech API on error.

```
toggle() →
  if listening: stop recording, send blob
  else: start MediaRecorder (audio/webm)

on stop →
  POST /api/v1/voice/transcribe (FormData with audio blob)
  → onResult(text)
  catch → fallback Web Speech API
```

States: `listening` (recording), `transcribing` (uploading/processing).

### useTTS (frontend/lib/hooks/use-voice.ts)

New function replacing direct Piper usage. Calls backend TTS endpoint, falls back to Piper WASM.

```
speak(text) →
  fetch GET /api/v1/voice/speak?text=...
  → create Audio from response blob → play
  catch → fallback usePiperTTS.speak(text)
```

States: `speaking`, `loading`.

### Component changes

- `message-bubble.tsx`: import `useTTS` from `use-voice` instead of `usePiperTTS` from `use-piper-tts`
- `chat-input.tsx`: no changes needed (useSTT interface stays the same)
- `use-piper-tts.ts`: kept as-is, used internally as fallback

## Testing

- Backend: test transcribe endpoint with sample audio file, test speak endpoint returns audio
- Frontend: manual test mic → transcribe → text in input, speaker → audio playback
- Fallback: disable VOICE_ENABLED flag → verify browser fallback works

## Acceptance Criteria

- STT accuracy >= 90% for Vietnamese conversational (inherits from Gemini model quality)
- TTS first byte latency < 500ms
- Fallback to browser APIs when backend unavailable
- Feature flag `VOICE_ENABLED` controls availability
- Audio upload max 10MB, TTS text max 2000 chars
