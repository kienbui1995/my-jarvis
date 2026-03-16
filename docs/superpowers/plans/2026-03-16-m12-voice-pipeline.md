# M12 Advanced Voice Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add backend STT (Gemini via LiteLLM) and TTS (Vertex AI via LiteLLM) endpoints with HTTP streaming, upgrade frontend hooks to use backend-first with browser fallback.

**Architecture:** Two new backend modules (`voice/stt.py`, `voice/tts.py`) behind a FastAPI router (`api/v1/voice.py`), calling LiteLLM Proxy's `gemini-stt` and `vertex-tts` models via OpenAI SDK. Frontend `use-voice.ts` rewritten to record audio blobs (MediaRecorder) and call backend endpoints, falling back to Web Speech API (STT) and Piper WASM (TTS) on failure.

**Tech Stack:** FastAPI, OpenAI Python SDK (async), LiteLLM Proxy, MediaRecorder API, Web Audio API

**Spec:** `docs/superpowers/specs/2026-03-16-m12-voice-pipeline-design.md`

---

## Chunk 1: Backend Voice Module

### Task 1: Config — add voice feature flags

**Files:**
- Modify: `backend/core/config.py:63-76`

- [ ] **Step 1: Add voice config fields**

Add after `TOOL_PERMISSIONS_ENABLED` (line 76):

```python
# Voice (M12)
VOICE_ENABLED: bool = True
VOICE_MAX_AUDIO_SIZE: int = 10 * 1024 * 1024  # 10MB
VOICE_TTS_MAX_CHARS: int = 2000
```

- [ ] **Step 2: Commit**

```bash
git add backend/core/config.py
git commit -m "feat(voice): add VOICE_ENABLED feature flag and limits"
```

---

### Task 2: STT module — transcribe audio via LiteLLM

**Files:**
- Create: `backend/voice/__init__.py`
- Create: `backend/voice/stt.py`
- Create: `backend/tests/test_voice.py`

- [ ] **Step 1: Create voice package**

`backend/voice/__init__.py` — empty file.

- [ ] **Step 2: Write failing test for transcribe**

`backend/tests/test_voice.py`:

```python
"""Tests for voice STT and TTS modules."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestSTT:
    @pytest.mark.asyncio
    async def test_transcribe_returns_text(self):
        mock_transcript = MagicMock()
        mock_transcript.text = "xin chao"

        with patch("voice.stt._client") as mock_client:
            mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcript)

            from voice.stt import transcribe
            result = await transcribe(b"fake-audio-bytes", "test.webm")

            assert result["text"] == "xin chao"
            assert result["language"] == "vi"
            mock_client.audio.transcriptions.create.assert_called_once_with(
                model="gemini-stt",
                file=("test.webm", b"fake-audio-bytes"),
                language="vi",
            )

    @pytest.mark.asyncio
    async def test_transcribe_propagates_error(self):
        with patch("voice.stt._client") as mock_client:
            mock_client.audio.transcriptions.create = AsyncMock(
                side_effect=Exception("API error")
            )
            from voice.stt import transcribe
            with pytest.raises(Exception, match="API error"):
                await transcribe(b"fake-audio", "test.webm")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd /home/kienbm/my-jarvis/backend && python -m pytest tests/test_voice.py::TestSTT -v`
Expected: FAIL (voice module doesn't exist yet)

- [ ] **Step 4: Implement stt.py**

`backend/voice/stt.py`:

```python
"""STT — transcribe audio via LiteLLM proxy (gemini-stt)."""
from openai import AsyncOpenAI

from core.config import settings

_client = AsyncOpenAI(api_key=settings.LITELLM_API_KEY, base_url=settings.LITELLM_BASE_URL)


async def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """Transcribe audio bytes to text. Returns {"text": ..., "language": "vi"}."""
    transcript = await _client.audio.transcriptions.create(
        model="gemini-stt",
        file=(filename, audio_bytes),
        language="vi",
    )
    return {"text": transcript.text, "language": "vi"}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd /home/kienbm/my-jarvis/backend && python -m pytest tests/test_voice.py::TestSTT -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/voice/__init__.py backend/voice/stt.py backend/tests/test_voice.py
git commit -m "feat(voice): add STT module — transcribe via gemini-stt"
```

---

### Task 3: TTS module — generate speech via LiteLLM

**Files:**
- Create: `backend/voice/tts.py`
- Modify: `backend/tests/test_voice.py`

- [ ] **Step 1: Write failing test for TTS**

Append to `backend/tests/test_voice.py`:

```python
class TestTTS:
    @pytest.mark.asyncio
    async def test_speak_stream_yields_chunks(self):
        mock_response = MagicMock()
        mock_response.content = b"\x00" * 20000  # 20KB fake audio

        with patch("voice.tts._client") as mock_client:
            mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

            from voice.tts import speak_stream
            chunks = []
            async for chunk in speak_stream("xin chao", "vi-VN"):
                chunks.append(chunk)

            assert len(chunks) == 3  # 20000 / 8192 = 2.44 -> 3 chunks
            assert b"".join(chunks) == b"\x00" * 20000
            mock_client.audio.speech.create.assert_called_once_with(
                model="vertex-tts",
                input="xin chao",
                voice="vi-VN",
                response_format="wav",
            )

    @pytest.mark.asyncio
    async def test_speak_stream_propagates_error(self):
        with patch("voice.tts._client") as mock_client:
            mock_client.audio.speech.create = AsyncMock(
                side_effect=Exception("TTS error")
            )
            from voice.tts import speak_stream
            with pytest.raises(Exception, match="TTS error"):
                async for _ in speak_stream("hello"):
                    pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/kienbm/my-jarvis/backend && python -m pytest tests/test_voice.py::TestTTS -v`
Expected: FAIL (voice.tts doesn't exist)

- [ ] **Step 3: Implement tts.py**

`backend/voice/tts.py`:

```python
"""TTS — generate speech via LiteLLM proxy (vertex-tts)."""
from typing import AsyncGenerator

from openai import AsyncOpenAI

from core.config import settings

_client = AsyncOpenAI(api_key=settings.LITELLM_API_KEY, base_url=settings.LITELLM_BASE_URL)

CHUNK_SIZE = 8192


async def speak_stream(text: str, voice: str = "vi-VN") -> AsyncGenerator[bytes, None]:
    """Generate speech and yield audio chunks for streaming response."""
    response = await _client.audio.speech.create(
        model="vertex-tts",
        input=text,
        voice=voice,
        response_format="wav",
    )
    content = response.content
    for i in range(0, len(content), CHUNK_SIZE):
        yield content[i:i + CHUNK_SIZE]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/kienbm/my-jarvis/backend && python -m pytest tests/test_voice.py::TestTTS -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/voice/tts.py backend/tests/test_voice.py
git commit -m "feat(voice): add TTS module — streaming audio via vertex-tts"
```

---

### Task 4: Voice API router — transcribe + speak endpoints

**Files:**
- Create: `backend/api/v1/voice.py`
- Modify: `backend/main.py:12-13` (import), `backend/main.py:101` (register router)
- Modify: `backend/tests/test_voice.py`

- [ ] **Step 1: Write failing tests for API endpoints**

Append to `backend/tests/test_voice.py`:

```python
class TestVoiceAPI:
    @pytest.mark.asyncio
    async def test_transcribe_unauthorized(self, client):
        resp = await client.post("/api/v1/voice/transcribe")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_speak_unauthorized(self, client):
        resp = await client.get("/api/v1/voice/speak", params={"text": "hello"})
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_transcribe_success(self, client):
        import uuid
        email = f"voice-{uuid.uuid4().hex[:6]}@jarvis.vn"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass1234", "name": "Voice"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("voice.stt._client") as mock_client:
            mock_transcript = MagicMock()
            mock_transcript.text = "xin chao"
            mock_client.audio.transcriptions.create = AsyncMock(return_value=mock_transcript)

            resp = await client.post(
                "/api/v1/voice/transcribe",
                headers=headers,
                files={"audio": ("test.webm", b"fake-audio", "audio/webm")},
            )
            assert resp.status_code == 200
            assert resp.json()["text"] == "xin chao"

    @pytest.mark.asyncio
    async def test_transcribe_too_large(self, client):
        import uuid
        email = f"voice-big-{uuid.uuid4().hex[:6]}@jarvis.vn"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass1234", "name": "Big"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        big_audio = b"\x00" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        resp = await client.post(
            "/api/v1/voice/transcribe",
            headers=headers,
            files={"audio": ("big.webm", big_audio, "audio/webm")},
        )
        assert resp.status_code == 413

    @pytest.mark.asyncio
    async def test_speak_success(self, client):
        import uuid
        email = f"voice-speak-{uuid.uuid4().hex[:6]}@jarvis.vn"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass1234", "name": "Speak"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("voice.tts._client") as mock_client:
            mock_response = MagicMock()
            mock_response.content = b"\x00\x01\x02\x03" * 100
            mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

            resp = await client.get(
                "/api/v1/voice/speak",
                params={"text": "xin chao"},
                headers=headers,
            )
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "audio/wav"
            assert len(resp.content) == 400

    @pytest.mark.asyncio
    async def test_speak_text_too_long(self, client):
        import uuid
        email = f"voice-long-{uuid.uuid4().hex[:6]}@jarvis.vn"
        reg = await client.post("/api/v1/auth/register", json={
            "email": email, "password": "pass1234", "name": "Long"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(
            "/api/v1/voice/speak",
            params={"text": "a" * 2001},
            headers=headers,
        )
        assert resp.status_code == 422  # FastAPI Query max_length validation
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/kienbm/my-jarvis/backend && python -m pytest tests/test_voice.py::TestVoiceAPI -v`
Expected: FAIL (voice router not registered)

- [ ] **Step 3: Create voice API router**

`backend/api/v1/voice.py`:

```python
"""Voice API — STT transcription and TTS streaming."""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from core.config import settings
from core.deps import get_current_user_id
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
    text: str = Query(..., max_length=settings.VOICE_TTS_MAX_CHARS),
    voice: str = Query("vi-VN"),
    user_id: str = Depends(get_current_user_id),
):
    if not settings.VOICE_ENABLED:
        raise HTTPException(503, "Voice is disabled")
    return StreamingResponse(speak_stream(text, voice), media_type="audio/wav")
```

- [ ] **Step 4: Register router in main.py**

In `backend/main.py`, add import alongside existing route imports (line 12-16 area):

```python
from api.v1 import voice
```

Add router registration after the feedback router (after line 101):

```python
app.include_router(voice.router, prefix=f"{_v1}/voice", tags=["voice"])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/kienbm/my-jarvis/backend && python -m pytest tests/test_voice.py::TestVoiceAPI -v`
Expected: PASS

- [ ] **Step 6: Run full test suite to verify no regressions**

Run: `cd /home/kienbm/my-jarvis/backend && python -m pytest tests/ -v`
Expected: All existing tests still pass

- [ ] **Step 7: Commit**

```bash
git add backend/api/v1/voice.py backend/main.py backend/tests/test_voice.py
git commit -m "feat(voice): add /voice/transcribe and /voice/speak API endpoints"
```

---

## Chunk 2: Frontend Voice Hooks + Integration

### Task 5: Rewrite useSTT — MediaRecorder + backend transcription + fallback

**Files:**
- Modify: `frontend/lib/hooks/use-voice.ts`

- [ ] **Step 1: Rewrite use-voice.ts with backend-first STT and TTS**

Replace entire contents of `frontend/lib/hooks/use-voice.ts`:

```typescript
"use client";
import { useState, useRef, useCallback } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// --- STT: MediaRecorder → backend /voice/transcribe → fallback Web Speech API ---

export function useSTT(onResult: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const fallbackWebSpeech = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    const rec = new SR();
    rec.lang = "vi-VN";
    rec.interimResults = false;
    rec.continuous = false;
    rec.onresult = (e: any) => onResult(e.results[0][0].transcript);
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    rec.start();
    setListening(true);
  }, [onResult]);

  const sendToBackend = useCallback(async (blob: Blob) => {
    setTranscribing(true);
    try {
      const form = new FormData();
      form.append("audio", blob, "recording.webm");
      const res = await fetch(`${API}/voice/transcribe`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: form,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.text) onResult(data.text);
    } catch {
      // Fallback: re-record with Web Speech API
      fallbackWebSpeech();
    } finally {
      setTranscribing(false);
    }
  }, [onResult, fallbackWebSpeech]);

  const toggle = useCallback(async () => {
    if (listening) {
      recorderRef.current?.stop();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        setListening(false);
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size > 0) sendToBackend(blob);
      };

      recorderRef.current = recorder;
      recorder.start();
      setListening(true);
    } catch {
      // MediaRecorder not available — fallback to Web Speech API
      fallbackWebSpeech();
    }
  }, [listening, sendToBackend, fallbackWebSpeech]);

  return { listening, transcribing, toggle };
}

// --- TTS: backend /voice/speak → fallback Piper WASM ---

export function useTTS() {
  const [speaking, setSpeaking] = useState(false);
  const [loading, setLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const speak = useCallback(async (text: string) => {
    if (speaking) {
      audioRef.current?.pause();
      setSpeaking(false);
      return;
    }

    const clean = text.replace(/[#*`>\[\]()!_~|]/g, "").replace(/\n+/g, ". ").trim();
    if (!clean) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({ text: clean.slice(0, 2000), voice: "vi-VN" });
      const res = await fetch(`${API}/voice/speak?${params}`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(url); };
      audio.onerror = () => { setSpeaking(false); URL.revokeObjectURL(url); };
      setSpeaking(true);
      setLoading(false);
      await audio.play();
    } catch {
      // Fallback to Piper WASM TTS
      setLoading(false);
      try {
        const { predict } = await import("@mintplex-labs/piper-tts-web");
        const blob = await predict({ voiceId: "vi_VN-vais1000-medium", text: clean });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(url); };
        audio.onerror = () => { setSpeaking(false); URL.revokeObjectURL(url); };
        setSpeaking(true);
        await audio.play();
      } catch {
        setSpeaking(false);
      }
    }
  }, [speaking]);

  const stop = useCallback(() => {
    audioRef.current?.pause();
    setSpeaking(false);
  }, []);

  return { speaking, loading, speak, stop };
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/lib/hooks/use-voice.ts
git commit -m "feat(voice): rewrite useSTT + useTTS with backend-first, browser fallback"
```

---

### Task 6: Update message-bubble to use new useTTS

**Files:**
- Modify: `frontend/components/chat/message-bubble.tsx:8,54`

- [ ] **Step 1: Replace usePiperTTS with useTTS**

In `frontend/components/chat/message-bubble.tsx`:

Change line 8 from:
```typescript
import { usePiperTTS } from "@/lib/hooks/use-piper-tts";
```
to:
```typescript
import { useTTS } from "@/lib/hooks/use-voice";
```

Change line 54 from:
```typescript
const { speaking, loading, speak } = usePiperTTS();
```
to:
```typescript
const { speaking, loading, speak } = useTTS();
```

- [ ] **Step 2: Verify chat-input.tsx needs no changes**

`frontend/components/chat/chat-input.tsx` already imports `useSTT` from `@/lib/hooks/use-voice`. The hook signature remains `{ listening, toggle }` plus new `transcribing` state. The component only uses `listening` and `toggle`, so no changes needed.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/chat/message-bubble.tsx
git commit -m "feat(voice): switch message-bubble from Piper WASM to backend TTS"
```

---

### Task 7: Add transcribing indicator to chat-input

**Files:**
- Modify: `frontend/components/chat/chat-input.tsx:10,48-53`

- [ ] **Step 1: Use transcribing state from useSTT**

In `frontend/components/chat/chat-input.tsx`:

Change line 10 from:
```typescript
const { listening, toggle: toggleMic } = useSTT((text) => { setValue((v) => v ? v + " " + text : text); });
```
to:
```typescript
const { listening, transcribing, toggle: toggleMic } = useSTT((text) => { setValue((v) => v ? v + " " + text : text); });
```

Change the mic button (lines 47-53) from:
```tsx
<button
  onClick={toggleMic}
  aria-label={listening ? "Dung ghi am" : "Nhap bang giong noi"}
  className={cn("p-2.5 rounded-full transition-colors shrink-0", listening ? "bg-[var(--accent-red)] text-white animate-pulse" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]")}
>
  {listening ? <MicOff size={18} /> : <Mic size={18} />}
</button>
```
to:
```tsx
<button
  onClick={toggleMic}
  disabled={transcribing}
  aria-label={transcribing ? "Dang nhan dang..." : listening ? "Dung ghi am" : "Nhap bang giong noi"}
  className={cn("p-2.5 rounded-full transition-colors shrink-0", transcribing ? "text-[var(--brand-primary)] animate-pulse" : listening ? "bg-[var(--accent-red)] text-white animate-pulse" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]")}
>
  {listening ? <MicOff size={18} /> : <Mic size={18} />}
</button>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/chat/chat-input.tsx
git commit -m "feat(voice): show transcribing state on mic button"
```

---

### Task 8: Final integration commit + env example update

**Files:**
- Modify: `backend/.env.example` (if exists) or project root `.env.example`

- [ ] **Step 1: Add voice config to .env.example**

Append to `.env.example` before the Sentry section:

```env
# --- Voice (M12) ---
VOICE_ENABLED=true
```

- [ ] **Step 2: Run backend lint**

Run: `cd /home/kienbm/my-jarvis/backend && ruff check .`
Expected: No errors

- [ ] **Step 3: Run full backend test suite**

Run: `cd /home/kienbm/my-jarvis/backend && python -m pytest tests/ -v`
Expected: All tests pass including new voice tests

- [ ] **Step 4: Run frontend lint**

Run: `cd /home/kienbm/my-jarvis/frontend && npm run lint`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add .env.example
git commit -m "feat(voice): M12 Advanced Voice Pipeline complete"
```
