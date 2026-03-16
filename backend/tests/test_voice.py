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
