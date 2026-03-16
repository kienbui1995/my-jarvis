"""Event bus — publish/consume events via Redis Streams."""
import json
import logging
import time

import core.redis as redis_pool

logger = logging.getLogger(__name__)

STREAM_KEY = "jarvis:events"
GROUP_NAME = "trigger-workers"
MAX_STREAM_LEN = 10000


async def emit(event_type: str, user_id: str, payload: dict | None = None) -> str | None:
    """Publish an event to the bus. Returns the event ID or None on failure.

    Usage: await emit("task.created", user_id, {"task_id": "...", "title": "..."})
    """
    r = redis_pool.get()
    event = {
        "type": event_type,
        "user_id": user_id,
        "payload": json.dumps(payload or {}),
        "ts": str(time.time()),
    }
    try:
        event_id = await r.xadd(STREAM_KEY, event, maxlen=MAX_STREAM_LEN)
        logger.debug(f"Event emitted: {event_type} user={user_id} id={event_id}")
        return event_id
    except Exception:
        logger.debug("Event emit failed", exc_info=True)
        return None


async def ensure_group() -> None:
    """Create consumer group if it doesn't exist."""
    r = redis_pool.get()
    try:
        await r.xgroup_create(STREAM_KEY, GROUP_NAME, id="0", mkstream=True)
    except Exception:
        pass  # Group already exists


async def consume(consumer_name: str = "worker-1", count: int = 10, block_ms: int = 5000):
    """Read new events from the stream as a consumer group member.

    Yields (event_id, {"type": ..., "user_id": ..., "payload": {...}}) tuples.
    """
    r = redis_pool.get()
    results = await r.xreadgroup(
        GROUP_NAME, consumer_name, {STREAM_KEY: ">"}, count=count, block=block_ms
    )
    for _stream, messages in results:
        for event_id, fields in messages:
            try:
                parsed = {
                    "type": fields["type"],
                    "user_id": fields["user_id"],
                    "payload": json.loads(fields.get("payload", "{}")),
                    "ts": fields.get("ts", ""),
                }
                yield event_id, parsed
            except Exception:
                logger.debug(f"Failed to parse event {event_id}", exc_info=True)
            # Acknowledge regardless to avoid reprocessing
            await r.xack(STREAM_KEY, GROUP_NAME, event_id)
