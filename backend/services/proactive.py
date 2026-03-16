"""Proactive scheduler — ARQ worker for event-driven triggers + cron jobs."""
import asyncio
import logging

from arq import cron
from arq.connections import RedisSettings

from channels.base import JarvisResponse
from channels.telegram import TelegramAdapter
from channels.zalo import ZaloAdapter
from channels.zalo_bot import ZaloBotAdapter
from core.config import settings
from db.models import Notification, User
from db.session import async_session
from services.event_bus import emit

logger = logging.getLogger(__name__)
zalo = ZaloAdapter()
zalo_bot = ZaloBotAdapter()
telegram = TelegramAdapter()


async def _send_to_user(user: User, content: str, notif_type: str = "briefing"):
    """Send proactive message via user's primary channel + save as notification."""
    async with async_session() as db:
        db.add(Notification(user_id=user.id, type=notif_type, content=content))
        await db.commit()

    resp = JarvisResponse(content=content)
    if user.zalo_id:
        await zalo.send_response(user.zalo_id, resp)
    if user.zalo_bot_id:
        await zalo_bot.send_response(user.zalo_bot_id, resp)
    if user.telegram_id:
        await telegram.send_response(user.telegram_id, resp)


# ── Cron jobs that emit events into the bus ──────────────────

async def cron_morning_briefing(ctx: dict):
    """Emit morning briefing event for all users."""
    from sqlalchemy import select

    from db.models import ProactiveTrigger
    async with async_session() as db:
        triggers = (await db.execute(
            select(ProactiveTrigger).where(
                ProactiveTrigger.trigger_type == "morning_briefing",
                ProactiveTrigger.enabled.is_(True),
            )
        )).scalars().all()
        for trigger in triggers:
            await emit("cron.morning_briefing", str(trigger.user_id), {})


async def cron_check_deadlines(ctx: dict):
    """Emit deadline check event for all users with deadline triggers."""
    from sqlalchemy import select

    from db.models import ProactiveTrigger
    async with async_session() as db:
        triggers = (await db.execute(
            select(ProactiveTrigger).where(
                ProactiveTrigger.trigger_type == "deadline_approaching",
                ProactiveTrigger.enabled.is_(True),
            )
        )).scalars().all()
        for trigger in triggers:
            await emit("cron.check_deadlines", str(trigger.user_id), {})


async def cron_scheduled_agents(ctx: dict):
    """Emit scheduled agent events for all users."""
    from sqlalchemy import select

    from db.models import ProactiveTrigger
    async with async_session() as db:
        triggers = (await db.execute(
            select(ProactiveTrigger).where(
                ProactiveTrigger.trigger_type == "scheduled_agent",
                ProactiveTrigger.enabled.is_(True),
            )
        )).scalars().all()
        for trigger in triggers:
            await emit("cron.scheduled_agent", str(trigger.user_id), {})


# ── Event consumer background task ──────────────────────────

async def _run_event_consumer(ctx: dict):
    """Background task: consume events and process triggers."""
    if not settings.PROACTIVE_ENGINE_ENABLED:
        logger.info("Proactive engine disabled, skipping event consumer")
        return

    # Import handlers to register them
    import services.handlers  # noqa: F401
    from services.trigger_engine import run_event_loop

    logger.info("Starting event consumer...")
    await run_event_loop(consumer_name="arq-worker")


# ── ARQ Worker Settings ─────────────────────────────────────

class WorkerSettings:
    """ARQ worker settings — referenced by docker-compose worker command."""
    from urllib.parse import urlparse as _urlparse
    _p = _urlparse(settings.REDIS_URL)
    redis_settings = RedisSettings(
        host=_p.hostname or "redis", port=_p.port or 6379,
        password=_p.password or None,
        database=int((_p.path or "/0").strip("/") or 0),
    )

    cron_jobs = [
        cron(cron_morning_briefing, hour=1, minute=0),    # 08:00 VN (UTC+7)
        cron(cron_check_deadlines, hour=7, minute=0),
        cron(cron_check_deadlines, hour=13, minute=0),
        cron(cron_check_deadlines, hour=19, minute=0),
        cron(cron_scheduled_agents, hour=1, minute=0),    # 08:00 VN
        cron(cron_scheduled_agents, hour=5, minute=0),    # 12:00 VN
        cron(cron_scheduled_agents, hour=11, minute=0),   # 18:00 VN
    ]

    @staticmethod
    async def on_startup(ctx: dict):
        """Start event consumer as a background task alongside ARQ."""
        ctx["event_consumer"] = asyncio.create_task(_run_event_consumer(ctx))
        logger.info("ARQ worker started with event consumer")

    @staticmethod
    async def on_shutdown(ctx: dict):
        """Cancel event consumer on shutdown."""
        task = ctx.get("event_consumer")
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("ARQ worker stopped")
