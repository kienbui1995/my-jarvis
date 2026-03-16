"""WhatsApp Business Cloud API adapter."""
import hashlib
import hmac
import logging

import httpx

from channels.base import ChannelAdapter, JarvisMessage, JarvisResponse
from core.config import settings

logger = logging.getLogger(__name__)

WA_API = "https://graph.facebook.com/v21.0"


class WhatsAppAdapter(ChannelAdapter):
    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

    async def parse_incoming(self, raw_payload: dict) -> JarvisMessage:
        entry = (raw_payload.get("entry") or [{}])[0]
        changes = (entry.get("changes") or [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        msg = messages[0] if messages else {}
        contacts = value.get("contacts", [])
        contact = contacts[0] if contacts else {}

        content = ""
        if msg.get("type") == "text":
            content = msg.get("text", {}).get("body", "")
        elif msg.get("type") == "image":
            content = msg.get("image", {}).get("caption", "[image]")

        return JarvisMessage(
            user_id=msg.get("from", ""),
            channel="whatsapp",
            content=content,
            metadata={
                "chat_id": msg.get("from", ""),
                "display_name": contact.get("profile", {}).get("name", ""),
                "message_id": msg.get("id", ""),
                "raw": raw_payload,
            },
        )

    async def send_response(self, recipient_id: str, response: JarvisResponse) -> None:
        url = f"{WA_API}/{settings.WHATSAPP_PHONE_ID}/messages"
        body = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": response.content[:4096]},
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=body, headers=self._headers)
            if resp.status_code != 200:
                logger.warning(f"WhatsApp send failed: {resp.status_code}")

    async def verify_webhook(self, payload: dict, headers: dict) -> bool:
        # WhatsApp uses X-Hub-Signature-256 for webhook verification
        signature = headers.get("x-hub-signature-256", "")
        if not signature or not settings.WHATSAPP_WEBHOOK_SECRET:
            return True  # dev mode
        import json
        body = json.dumps(payload, separators=(",", ":")).encode()
        expected = "sha256=" + hmac.new(
            settings.WHATSAPP_WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    async def send_greeting(self, phone: str) -> None:
        await self.send_response(
            phone,
            JarvisResponse(
                content="Chào bạn! Tôi là JARVIS 🤖\nGửi /link <mã> để liên kết."
            ),
        )
