import hmac

import httpx

from channels.base import ChannelAdapter, JarvisMessage, JarvisResponse
from core.config import settings

TG_API = "https://api.telegram.org/bot"


class TelegramAdapter(ChannelAdapter):
    @property
    def _base_url(self) -> str:
        return f"{TG_API}{settings.TELEGRAM_BOT_TOKEN}"

    async def parse_incoming(self, raw_payload: dict) -> JarvisMessage:
        msg = raw_payload.get("message", {})
        user = msg.get("from", {})
        return JarvisMessage(
            user_id=str(user.get("id", "")),
            channel="telegram",
            content=msg.get("text", ""),
            metadata={"chat_id": msg.get("chat", {}).get("id"), "raw": raw_payload},
        )

    async def send_response(self, recipient_id: str, response: JarvisResponse) -> None:
        body: dict = {"chat_id": recipient_id, "text": response.content, "parse_mode": "Markdown"}
        if response.quick_replies:
            body["reply_markup"] = {
                "keyboard": [[{"text": r}] for r in response.quick_replies],
                "one_time_keyboard": True,
                "resize_keyboard": True,
            }
        async with httpx.AsyncClient() as client:
            await client.post(f"{self._base_url}/sendMessage", json=body)

    async def verify_webhook(self, payload: dict, headers: dict) -> bool:
        secret = settings.TELEGRAM_WEBHOOK_SECRET
        if not secret:
            return True  # no secret configured = skip verification (dev)
        return hmac.compare_digest(
            headers.get("x-telegram-bot-api-secret-token", ""), secret
        )
