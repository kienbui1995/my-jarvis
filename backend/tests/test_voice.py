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
