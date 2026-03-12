"""M10 Supervision — heartbeat, watchdog, graceful recovery.

- Heartbeat: Redis key per session, 10s interval, 30s TTL
- Watchdog: max 5min session duration, auto-terminate
- Recovery: detect stale sessions, clean up
"""
import asyncio
import logging
import time
from uuid import uuid4

import core.redis as redis_pool
from core.config import settings

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 10  # seconds
HEARTBEAT_TTL = 30  # seconds
MAX_SESSION_DURATION = 300  # 5 minutes


class SessionSupervisor:
    """Manages a single agent session lifecycle."""

    def __init__(self, user_id: str, conversation_id: str):
        self.session_id = str(uuid4())
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.started_at = time.monotonic()
        self._heartbeat_task: asyncio.Task | None = None

    @property
    def _key(self) -> str:
        return f"heartbeat:{self.session_id}"

    async def start(self) -> str:
        """Start heartbeat. Returns session_id."""
        if not settings.SUPERVISION_ENABLED:
            return self.session_id
        r = redis_pool.get()
        await r.setex(self._key, HEARTBEAT_TTL, f"{self.user_id}:{self.conversation_id}")
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        return self.session_id

    async def stop(self):
        """Stop heartbeat and clean up."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        try:
            r = redis_pool.get()
            await r.delete(self._key)
        except Exception:
            pass

    def check_timeout(self) -> bool:
        """Returns True if session exceeded max duration."""
        return (time.monotonic() - self.started_at) > MAX_SESSION_DURATION

    async def _heartbeat_loop(self):
        """Background task: refresh heartbeat key every HEARTBEAT_INTERVAL."""
        r = redis_pool.get()
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                await r.setex(self._key, HEARTBEAT_TTL, f"{self.user_id}:{self.conversation_id}")
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.debug("Heartbeat loop error", exc_info=True)


async def cleanup_stale_sessions() -> int:
    """Count active heartbeat sessions. Stale ones auto-expire via Redis TTL."""
    if not settings.SUPERVISION_ENABLED:
        return 0
    r = redis_pool.get()
    cursor, count = "0", 0
    while True:
        cursor, keys = await r.scan(cursor=cursor, match="heartbeat:*", count=100)
        count += len(keys)
        if cursor == "0" or cursor == 0:
            break
    logger.info(f"Active supervised sessions: {count}")
    return count
