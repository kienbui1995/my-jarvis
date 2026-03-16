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
