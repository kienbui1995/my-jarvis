"""Discord Bot adapter — Interactions API (webhook mode)."""
import logging

import httpx
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from channels.base import ChannelAdapter, JarvisMessage, JarvisResponse
from core.config import settings

logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"


class DiscordAdapter(ChannelAdapter):
    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}"}

    async def parse_incoming(self, raw_payload: dict) -> JarvisMessage:
        # Handle interaction (slash command or message component)
        if raw_payload.get("type") == 1:
            # Ping — handled separately
            return JarvisMessage(user_id="", channel="discord", content="",
                                 metadata={"type": "ping"})

        # Message create event (from gateway or webhook)
        data = raw_payload.get("data", raw_payload)
        user = data.get("author", data.get("member", {}).get("user", {}))
        options = data.get("options", [])

        # Slash command: extract "message" option
        content = ""
        if options:
            for opt in options:
                if opt.get("name") == "message":
                    content = opt.get("value", "")
        else:
            content = data.get("content", "")

        return JarvisMessage(
            user_id=user.get("id", ""),
            channel="discord",
            content=content,
            metadata={
                "chat_id": data.get("channel_id", ""),
                "guild_id": data.get("guild_id", ""),
                "display_name": user.get("username", ""),
                "interaction_id": raw_payload.get("id", ""),
                "interaction_token": raw_payload.get("token", ""),
                "raw": raw_payload,
            },
        )

    async def send_response(self, recipient_id: str, response: JarvisResponse) -> None:
        # Split long messages (Discord 2000 char limit)
        content = response.content
        chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]

        async with httpx.AsyncClient(timeout=10) as client:
            for chunk in chunks:
                resp = await client.post(
                    f"{DISCORD_API}/channels/{recipient_id}/messages",
                    json={"content": chunk},
                    headers=self._headers,
                )
                if resp.status_code not in (200, 201):
                    logger.warning(f"Discord send failed: {resp.status_code}")

    async def send_interaction_response(
        self, interaction_id: str, interaction_token: str, content: str,
    ) -> None:
        """Respond to a slash command interaction."""
        url = f"{DISCORD_API}/interactions/{interaction_id}/{interaction_token}/callback"
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={
                "type": 4,
                "data": {"content": content[:2000]},
            })

    async def verify_webhook(self, payload: dict, headers: dict) -> bool:
        public_key = settings.DISCORD_PUBLIC_KEY
        if not public_key:
            return True

        signature = headers.get("x-signature-ed25519", "")
        timestamp = headers.get("x-signature-timestamp", "")

        try:
            import json
            body = json.dumps(payload, separators=(",", ":"))
            verify_key = VerifyKey(bytes.fromhex(public_key))
            verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
            return True
        except (BadSignatureError, Exception):
            return False
