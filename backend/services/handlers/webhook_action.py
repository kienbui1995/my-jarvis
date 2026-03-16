"""Webhook action trigger — call external URL when event fires."""
import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ProactiveTrigger
from services.trigger_engine import TriggerHandler, register_handler

logger = logging.getLogger(__name__)


@register_handler
class WebhookActionHandler(TriggerHandler):
    TRIGGER_TYPE = "webhook_action"
    LISTENS_TO = [
        "task.created", "task.updated",
        "calendar.created", "expense.created",
        "agent_task.completed",
    ]

    async def should_fire(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> bool:
        config = trigger.config or {}
        # Fire if event type matches configured events (or all events if not specified)
        listen_events = config.get("events", [])
        if listen_events and event["type"] not in listen_events:
            return False
        return bool(config.get("url"))

    async def build_message(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> str:
        """Call webhook URL with event data. Returns empty (no user notification)."""
        config = trigger.config or {}
        url = config.get("url", "")
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})

        payload = {
            "event_type": event["type"],
            "user_id": event.get("user_id", ""),
            "payload": event.get("payload", {}),
            "trigger_id": str(trigger.id),
        }

        retries = 3
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.request(
                        method, url, json=payload, headers=headers,
                    )
                    if resp.status_code < 400:
                        logger.info(f"Webhook OK: {url} ({resp.status_code})")
                        return ""  # No user notification for webhooks
                    logger.warning(f"Webhook {resp.status_code}: {url}")
            except Exception as e:
                logger.warning(f"Webhook attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"Webhook failed after {retries} attempts: {url}")
        return ""  # Silent failure — don't spam user
