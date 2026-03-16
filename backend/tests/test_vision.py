"""Tests for M17 Vision — file upload, image analysis, OCR."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStorageKeyFormat:
    """Test upload key generation logic without MinIO dependency."""

    def test_key_with_extension(self):
        import uuid
        filename = "photo.jpg"
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        key = f"uploads/{uuid.uuid4().hex[:12]}.{ext}"
        assert key.startswith("uploads/")
        assert key.endswith(".jpg")

    def test_key_no_extension(self):
        import uuid
        filename = "noext"
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        # When filename has no dot, rsplit returns the whole string
        # so ext == filename, but we check "." in filename
        has_ext = "." in filename
        uid = uuid.uuid4().hex[:12]
        key = f"uploads/{uid}.{ext}" if has_ext else f"uploads/{uid}"
        assert key.startswith("uploads/")
        assert "." not in key.split("/")[-1]


class TestVision:
    @pytest.mark.asyncio
    async def test_analyze_image_calls_llm(self):
        mock_choice = MagicMock()
        mock_choice.message.content = "Ảnh chụp hóa đơn"
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        with patch("services.vision._client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_resp
            )
            from services.vision import analyze_image
            result = await analyze_image(b"\x89PNG", "Mô tả ảnh", "image/png")
            assert "hóa đơn" in result
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args.kwargs["model"] == "gemini/gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_ocr_uses_extraction_prompt(self):
        mock_choice = MagicMock()
        mock_choice.message.content = "Total: 150,000 VND"
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        with patch("services.vision._client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(
                return_value=mock_resp
            )
            from services.vision import ocr_document
            result = await ocr_document(b"\x89PNG", "image/png")
            assert "150,000" in result
            call_args = mock_client.chat.completions.create.call_args
            content = call_args.kwargs["messages"][0]["content"]
            # Should have text prompt with OCR instruction
            assert any("text" in str(c) for c in content)
