"""Tests for voice STT, TTS modules and API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Ensure test settings are applied before any app import
from core.config import settings
settings.VOICE_ENABLED = True


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

        big_audio = b"\x00" * (10 * 1024 * 1024 + 1)
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
        assert resp.status_code == 422
