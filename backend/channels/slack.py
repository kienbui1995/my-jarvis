"""Slack Bot adapter — Events API + Web API."""
import hashlib
import hmac
import logging
import time

import httpx

from channels.base import ChannelAdapter, JarvisMessage, JarvisResponse
from core.config import settings

logger = logging.getLogger(__name__)

SLACK_API = "https://slack.com/api"


class SlackAdapter(ChannelAdapter):
    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"}

    async def parse_incoming(self, raw_payload: dict) -> JarvisMessage:
        event = raw_payload.get("event", {})
        return JarvisMessage(
            user_id=event.get("user", ""),
            channel="slack",
            content=event.get("text", ""),
            metadata={
                "chat_id": event.get("channel", ""),
                "thread_ts": event.get("thread_ts") or event.get("ts", ""),
                "team_id": raw_payload.get("team_id", ""),
                "event_type": event.get("type", ""),
                "raw": raw_payload,
            },
        )

    async def send_response(self, recipient_id: str, response: JarvisResponse) -> None:
        # recipient_id = "channel_id" or "channel_id:thread_ts"
        parts = recipient_id.split(":", 1)
        channel = parts[0]
        thread_ts = parts[1] if len(parts) > 1 else None

        body: dict = {"channel": channel, "text": response.content}
        if thread_ts:
            body["thread_ts"] = thread_ts

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{SLACK_API}/chat.postMessage",
                json=body, headers=self._headers,
            )
            if resp.status_code != 200:
                logger.warning(f"Slack send failed: {resp.status_code}")

    async def verify_webhook(self, payload: dict, headers: dict) -> bool:
        # Slack signing secret verification
        secret = settings.SLACK_SIGNING_SECRET
        if not secret:
            return True

        timestamp = headers.get("x-slack-request-timestamp", "")
        sig = headers.get("x-slack-signature", "")

        # Reject old timestamps (>5 min)
        if abs(time.time() - int(timestamp or 0)) > 300:
            return False

        import json
        body = json.dumps(payload, separators=(",", ":"))
        base = f"v0:{timestamp}:{body}"
        expected = "v0=" + hmac.new(
            secret.encode(), base.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(sig, expected)
