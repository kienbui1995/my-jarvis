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
