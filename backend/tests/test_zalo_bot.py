"""Tests for Zalo Bot Platform — adapter + webhook endpoint."""
import pytest
from unittest.mock import AsyncMock, patch

from channels.zalo_bot import ZaloBotAdapter
from channels.base import JarvisResponse


# --- Adapter unit tests ---

class TestZaloBotAdapter:
    @pytest.fixture
    def adapter(self):
        return ZaloBotAdapter()

    @pytest.mark.asyncio
    async def test_parse_text_message(self, adapter):
        payload = {
            "ok": True,
            "result": {
                "event_name": "message.text.received",
                "message": {
                    "from": {"id": "user123", "display_name": "Ted", "is_bot": False},
                    "chat": {"id": "chat456", "chat_type": "PRIVATE"},
                    "text": "Xin chào",
                    "message_id": "msg789",
                    "date": 1750316131602,
                },
            },
        }
        msg = await adapter.parse_incoming(payload)
        assert msg.user_id == "user123"
        assert msg.channel == "zalo_bot"
        assert msg.content == "Xin chào"
        assert msg.metadata["chat_id"] == "chat456"
        assert msg.metadata["display_name"] == "Ted"
        assert msg.metadata["event"] == "message.text.received"

    @pytest.mark.asyncio
    async def test_parse_image_message(self, adapter):
        payload = {
            "ok": True,
            "result": {
                "event_name": "message.image.received",
                "message": {
                    "from": {"id": "u1", "display_name": "A", "is_bot": False},
                    "chat": {"id": "c1", "chat_type": "PRIVATE"},
                    "photo": "https://example.com/img.jpg",
                    "caption": "Ảnh đẹp",
                    "message_id": "m1",
                    "date": 1,
                },
            },
        }
        msg = await adapter.parse_incoming(payload)
        assert msg.content == "Ảnh đẹp"  # caption takes priority
        assert msg.metadata["photo"] == "https://example.com/img.jpg"

    @pytest.mark.asyncio
    async def test_parse_image_no_caption(self, adapter):
        payload = {
            "ok": True,
            "result": {
                "event_name": "message.image.received",
                "message": {
                    "from": {"id": "u1", "display_name": "A", "is_bot": False},
                    "chat": {"id": "c1", "chat_type": "PRIVATE"},
                    "photo": "https://example.com/img.jpg",
                    "message_id": "m1",
                    "date": 1,
                },
            },
        }
        msg = await adapter.parse_incoming(payload)
        assert "img.jpg" in msg.content  # fallback to [Ảnh: url]

    @pytest.mark.asyncio
    async def test_parse_sticker_returns_empty(self, adapter):
        payload = {
            "ok": True,
            "result": {
                "event_name": "message.sticker.received",
                "message": {
                    "from": {"id": "u1", "display_name": "A", "is_bot": False},
                    "chat": {"id": "c1", "chat_type": "PRIVATE"},
                    "sticker": "abc123",
                    "url": "https://stickers.zaloapp.com/abc",
                    "message_id": "m1",
                    "date": 1,
                },
            },
        }
        msg = await adapter.parse_incoming(payload)
        assert msg.content == ""
        assert msg.metadata["sticker"] == "abc123"

    @pytest.mark.asyncio
    async def test_parse_unsupported_returns_empty(self, adapter):
        payload = {
            "ok": True,
            "result": {
                "event_name": "message.unsupported.received",
                "message": {
                    "from": {"id": "u1", "display_name": "A", "is_bot": False},
                    "chat": {"id": "c1", "chat_type": "PRIVATE"},
                    "message_id": "m1",
                    "date": 1,
                },
            },
        }
        msg = await adapter.parse_incoming(payload)
        assert msg.content == ""

    @pytest.mark.asyncio
    async def test_verify_webhook_valid(self, adapter):
        with patch("channels.zalo_bot.settings") as mock_settings:
            mock_settings.ZALO_BOT_SECRET_TOKEN = "my-secret"
            result = await adapter.verify_webhook({}, {"x-bot-api-secret-token": "my-secret"})
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_webhook_invalid(self, adapter):
        with patch("channels.zalo_bot.settings") as mock_settings:
            mock_settings.ZALO_BOT_SECRET_TOKEN = "my-secret"
            result = await adapter.verify_webhook({}, {"x-bot-api-secret-token": "wrong"})
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_webhook_no_secret(self, adapter):
        with patch("channels.zalo_bot.settings") as mock_settings:
            mock_settings.ZALO_BOT_SECRET_TOKEN = ""
            result = await adapter.verify_webhook({}, {})
            assert result is False

    @pytest.mark.asyncio
    async def test_send_response_splits_long_text(self, adapter):
        adapter._post = AsyncMock(return_value={"ok": True})
        long_text = "A" * 3500
        await adapter.send_response("chat1", JarvisResponse(content=long_text))
        # 1 typing + 2 message chunks (2000 + 1500)
        assert adapter._post.call_count == 3
        methods = [c.args[0] for c in adapter._post.call_args_list]
        assert methods == ["sendChatAction", "sendMessage", "sendMessage"]

    @pytest.mark.asyncio
    async def test_send_sticker(self, adapter):
        adapter._post = AsyncMock(return_value={"ok": True})
        await adapter.send_sticker("chat1", "sticker123")
        adapter._post.assert_called_once_with("sendSticker", {"chat_id": "chat1", "sticker": "sticker123"})

    @pytest.mark.asyncio
    async def test_send_photo_with_caption(self, adapter):
        adapter._post = AsyncMock(return_value={"ok": True})
        await adapter.send_photo("chat1", "https://img.com/a.jpg", "caption")
        adapter._post.assert_called_once_with("sendPhoto", {
            "chat_id": "chat1", "photo": "https://img.com/a.jpg", "caption": "caption",
        })


# --- Webhook endpoint tests ---

class TestZaloBotWebhook:
    @pytest.mark.asyncio
    async def test_rejects_invalid_token(self, client):
        r = await client.post("/api/v1/webhooks/zalo-bot", json={"ok": True}, headers={})
        assert r.json().get("error") == "invalid token"

    @pytest.mark.asyncio
    @patch("api.v1.webhooks.zalo_bot")
    async def test_accepts_valid_text_message(self, mock_bot, client):
        from channels.base import JarvisMessage
        mock_bot.verify_webhook = AsyncMock(return_value=True)
        mock_bot.parse_incoming = AsyncMock(return_value=JarvisMessage(
            user_id="u1", channel="zalo_bot", content="hello",
            metadata={"event": "message.text.received", "chat_id": "c1"},
        ))
        r = await client.post("/api/v1/webhooks/zalo-bot", json={"ok": True})
        assert r.json() == {"status": "ok"}

    @pytest.mark.asyncio
    @patch("api.v1.webhooks.zalo_bot")
    async def test_sticker_returns_ok(self, mock_bot, client):
        from channels.base import JarvisMessage
        mock_bot.verify_webhook = AsyncMock(return_value=True)
        mock_bot.parse_incoming = AsyncMock(return_value=JarvisMessage(
            user_id="u1", channel="zalo_bot", content="",
            metadata={"event": "message.sticker.received", "chat_id": "c1", "sticker": "abc"},
        ))
        mock_bot.send_response = AsyncMock()
        r = await client.post("/api/v1/webhooks/zalo-bot", json={"ok": True})
        assert r.json() == {"status": "ok"}
