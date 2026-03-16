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
