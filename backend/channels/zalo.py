"""Zalo OA adapter — text, buttons, list, quick replies via OA API v3."""
import hashlib
import hmac
import logging

import httpx

from channels.base import ChannelAdapter, JarvisMessage, JarvisResponse
from core.config import settings

logger = logging.getLogger(__name__)
ZALO_API = "https://openapi.zalo.me/v3.0/oa"


class ZaloAdapter(ChannelAdapter):
    """Full Zalo OA integration with rich message support."""

    def _headers(self):
        return {"access_token": settings.ZALO_OA_ACCESS_TOKEN, "Content-Type": "application/json"}

    async def _send(self, body: dict) -> dict | None:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{ZALO_API}/message/cs", json=body, headers=self._headers())
                return r.json()
        except Exception:
            logger.exception("Zalo send failed")
            return None

    # --- Parse incoming ---

    async def parse_incoming(self, raw_payload: dict) -> JarvisMessage:
        event = raw_payload.get("event_name", "")
        sender = raw_payload.get("sender", {})
        msg_data = raw_payload.get("message", {})
        return JarvisMessage(
            user_id=sender.get("id", ""),
            channel="zalo",
            content=msg_data.get("text", ""),
            attachments=msg_data.get("attachments", []),
            metadata={"event": event, "raw": raw_payload},
        )

    # --- Send responses ---

    async def send_response(self, recipient_id: str, response: JarvisResponse) -> None:
        """Smart send — uses buttons/quick_replies if provided, else plain text."""
        if response.metadata.get("buttons"):
            await self.send_buttons(recipient_id, response.content, response.metadata["buttons"])
        elif response.quick_replies:
            await self.send_quick_replies(recipient_id, response.content, response.quick_replies)
        else:
            await self.send_text(recipient_id, response.content)

    async def send_text(self, recipient_id: str, text: str) -> None:
        await self._send({
            "recipient": {"user_id": recipient_id},
            "message": {"text": text},
        })

    async def send_buttons(self, recipient_id: str, text: str, buttons: list[dict]) -> None:
        """Send message with action buttons. buttons: [{"title": "...", "payload": "..."}]"""
        elements = [{"title": b["title"], "type": "oa.open.sms", "payload": b.get("payload", b["title"])} for b in buttons[:5]]
        await self._send({
            "recipient": {"user_id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": text,
                        "buttons": elements,
                    },
                },
            },
        })

    async def send_quick_replies(self, recipient_id: str, text: str, replies: list[str]) -> None:
        """Send text with quick reply chips."""
        await self._send({
            "recipient": {"user_id": recipient_id},
            "message": {
                "text": text,
                "quick_replies": [{"type": "text", "payload": r, "title": r} for r in replies[:10]],
            },
        })

    async def send_list(self, recipient_id: str, header: str, items: list[dict]) -> None:
        """Send list message. items: [{"title": "...", "subtitle": "...", "image_url"?: "..."}]"""
        elements = [
            {"title": it["title"], "subtitle": it.get("subtitle", ""), "image_url": it.get("image_url", "")}
            for it in items[:5]
        ]
        await self._send({
            "recipient": {"user_id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {"template_type": "list", "elements": elements},
                },
            },
        })

    # --- OA Features ---

    async def send_greeting(self, user_id: str) -> None:
        """Welcome message when user follows OA."""
        await self.send_quick_replies(
            user_id,
            "Chào bạn! 🤖 Tôi là JARVIS — trợ lý AI cá nhân.\n\nTôi có thể giúp bạn quản lý task, lịch hẹn, chi tiêu, và tìm kiếm thông tin. Hãy thử nhắn cho tôi!",
            ["Tạo task", "Xem lịch hôm nay", "Chi tiêu hôm nay", "Hướng dẫn"],
        )

    async def set_persistent_menu(self) -> None:
        """Set OA persistent menu (call once during setup)."""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{ZALO_API}/menu",
                    json={"menu": [
                        {"title": "📋 Tasks", "type": "oa.open.sms", "payload": "Xem tasks"},
                        {"title": "📅 Lịch hôm nay", "type": "oa.open.sms", "payload": "Xem lịch hôm nay"},
                        {"title": "💰 Chi tiêu", "type": "oa.open.sms", "payload": "Chi tiêu hôm nay"},
                        {"title": "🔔 Nhắc nhở", "type": "oa.open.sms", "payload": "Nhắc nhở sắp tới"},
                    ]},
                    headers=self._headers(),
                )
                logger.info("Zalo persistent menu set")
        except Exception:
            logger.exception("Failed to set Zalo menu")

    # --- Webhook verification ---

    async def verify_webhook(self, payload: dict, headers: dict) -> bool:
        secret = settings.ZALO_OA_SECRET_KEY
        if not secret:
            return False
        mac = headers.get("x-zalooa-signature", "")
        expected = hmac.new(secret.encode(), str(payload).encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, expected)
