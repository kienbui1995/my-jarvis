"""Zalo Bot Platform adapter — bot.zapps.me API."""
import logging

import httpx

from channels.base import ChannelAdapter, JarvisMessage, JarvisResponse
from core.config import settings

logger = logging.getLogger(__name__)
BOT_API = "https://bot-api.zaloplatforms.com"


class ZaloBotAdapter(ChannelAdapter):
    """Zalo Bot Platform — Bot Token auth, Telegram-like pattern."""

    @property
    def _base(self):
        return f"{BOT_API}/bot{settings.ZALO_BOT_TOKEN}"

    async def _post(self, method: str, body: dict) -> dict | None:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{self._base}/{method}", json=body)
                return r.json()
        except Exception:
            logger.exception(f"Zalo Bot API {method} failed")
            return None

    async def parse_incoming(self, raw_payload: dict) -> JarvisMessage:
        result = raw_payload.get("result", {})
        event = result.get("event_name", "")
        msg = result.get("message", {})
        sender = msg.get("from", {})
        chat = msg.get("chat", {})

        # Extract content based on event type
        if event == "message.text.received":
            content = msg.get("text", "")
        elif event == "message.image.received":
            caption = msg.get("caption", "")
            photo = msg.get("photo", "")
            content = caption or f"[Ảnh: {photo}]"
        elif event == "message.sticker.received":
            content = ""  # Stickers don't need AI processing
        elif event == "message.unsupported.received":
            content = ""  # Protected users — don't process
        else:
            content = ""

        return JarvisMessage(
            user_id=sender.get("id", ""),
            channel="zalo_bot",
            content=content,
            metadata={
                "event": event,
                "chat_id": chat.get("id", ""),
                "chat_type": chat.get("chat_type", "PRIVATE"),
                "display_name": sender.get("display_name", ""),
                "message_id": msg.get("message_id", ""),
                "photo": msg.get("photo", ""),
                "sticker": msg.get("sticker", ""),
            },
        )

    async def send_response(self, recipient_id: str, response: JarvisResponse) -> None:
        await self._post("sendChatAction", {"chat_id": recipient_id, "action": "typing"})
        text = response.content
        while text:
            chunk, text = text[:2000], text[2000:]
            await self._post("sendMessage", {"chat_id": recipient_id, "text": chunk})

    async def send_photo(self, chat_id: str, photo_url: str, caption: str = "") -> None:
        body = {"chat_id": chat_id, "photo": photo_url}
        if caption:
            body["caption"] = caption
        await self._post("sendPhoto", body)

    async def send_sticker(self, chat_id: str, sticker_id: str) -> None:
        await self._post("sendSticker", {"chat_id": chat_id, "sticker": sticker_id})

    async def verify_webhook(self, payload: dict, headers: dict) -> bool:
        secret = settings.ZALO_BOT_SECRET_TOKEN
        if not secret:
            return False
        return headers.get("x-bot-api-secret-token", "") == secret
