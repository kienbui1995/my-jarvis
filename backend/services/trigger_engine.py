"""Trigger engine — handler base class, registry, and worker loop."""
import logging
from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ProactiveTrigger, User
from db.session import async_session
from services.event_bus import consume, ensure_group

logger = logging.getLogger(__name__)

# ── Handler base class ──────────────────────────────────────

class TriggerHandler(ABC):
    """Base class for all trigger handlers.

    To create a new trigger:
    1. Create a file in services/handlers/
    2. Subclass TriggerHandler
    3. Set TRIGGER_TYPE and LISTENS_TO
    4. Implement should_fire() and build_message()
    5. Decorate with @register_handler
    """

    TRIGGER_TYPE: str = ""
    LISTENS_TO: list[str] = []  # Event types this handler cares about

    @abstractmethod
    async def should_fire(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> bool:
        """Return True if this trigger should fire for the given event."""

    @abstractmethod
    async def build_message(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> str:
        """Build the notification message to send to the user."""


# ── Registry ────────────────────────────────────────────────

_registry: dict[str, TriggerHandler] = {}
_event_to_handlers: dict[str, list[TriggerHandler]] = {}


def register_handler(cls: type[TriggerHandler]) -> type[TriggerHandler]:
    """Decorator to register a trigger handler."""
    instance = cls()
    _registry[instance.TRIGGER_TYPE] = instance
    for event_type in instance.LISTENS_TO:
        _event_to_handlers.setdefault(event_type, []).append(instance)
    logger.info(f"Registered trigger handler: {instance.TRIGGER_TYPE} -> {instance.LISTENS_TO}")
    return cls


def get_handlers_for_event(event_type: str) -> list[TriggerHandler]:
    """Get all handlers that listen to a given event type."""
    return _event_to_handlers.get(event_type, [])


def get_all_trigger_types() -> list[str]:
    """Get all registered trigger type names."""
    return list(_registry.keys())


# ── Worker loop ─────────────────────────────────────────────

async def _fire_trigger(handler: TriggerHandler, event: dict, trigger: ProactiveTrigger,
                        user: User, db: AsyncSession) -> None:
    """Execute a single trigger: build message + send to user."""
    from datetime import datetime

    from services.proactive import _send_to_user

    message = await handler.build_message(event, trigger, db)
    if not message:
        return

    await _send_to_user(user, message, trigger.trigger_type)
    trigger.last_fired = datetime.utcnow()
    await db.commit()
    logger.info(f"Trigger fired: {trigger.trigger_type} user={user.id}")


async def process_event(event: dict) -> None:
    """Match a single event against all relevant triggers and fire them."""
    handlers = get_handlers_for_event(event["type"])
    if not handlers:
        return

    user_id = event.get("user_id", "")
    if not user_id:
        return

    async with async_session() as db:
        for handler in handlers:
            # Find enabled triggers of this type for this user
            triggers = (await db.execute(
                select(ProactiveTrigger).where(
                    ProactiveTrigger.user_id == UUID(user_id),
                    ProactiveTrigger.trigger_type == handler.TRIGGER_TYPE,
                    ProactiveTrigger.enabled.is_(True),
                )
            )).scalars().all()

            for trigger in triggers:
                try:
                    if await handler.should_fire(event, trigger, db):
                        user = await db.get(User, trigger.user_id)
                        if user:
                            await _fire_trigger(handler, event, trigger, user, db)
                except Exception:
                    logger.exception(
                        f"Handler {handler.TRIGGER_TYPE} failed: {event['type']}"
                    )


async def run_event_loop(consumer_name: str = "worker-1") -> None:
    """Main worker loop: consume events from bus and process them.

    Called from ARQ worker on_startup. Runs until cancelled.
    """
    await ensure_group()
    logger.info(f"Trigger engine started (consumer={consumer_name})")

    while True:
        try:
            async for _event_id, event in consume(consumer_name):
                await process_event(event)
        except Exception:
            logger.exception("Event loop error, restarting...")
            import asyncio
            await asyncio.sleep(1)
