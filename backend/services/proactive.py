"""Proactive scheduler — ARQ worker for morning briefings + deadline reminders."""
import logging
from datetime import datetime, timedelta

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from channels.zalo import ZaloAdapter
from channels.zalo_bot import ZaloBotAdapter
from channels.telegram import TelegramAdapter
from channels.base import JarvisResponse
from core.config import settings
from db.models import User, Task, CalendarEvent, ProactiveTrigger
from db.session import async_session
from llm.gateway import get_llm

logger = logging.getLogger(__name__)
zalo = ZaloAdapter()
zalo_bot = ZaloBotAdapter()
telegram = TelegramAdapter()

BRIEFING_PROMPT = """Tạo bản tóm tắt buổi sáng ngắn gọn (tối đa 150 từ) bằng tiếng Việt cho user.

Tasks hôm nay:
{tasks}

Lịch hôm nay:
{events}

Phong cách: thân thiện, động viên, đi thẳng vào trọng tâm."""


async def _send_to_user(user: User, content: str, notif_type: str = "briefing"):
    """Send proactive message via user's primary channel + save as notification."""
    # Always save to notifications table (works for web + all channels)
    from db.models import Notification
    async with async_session() as db:
        db.add(Notification(user_id=user.id, type=notif_type, content=content))
        await db.commit()

    # Also push via external channels if connected
    resp = JarvisResponse(content=content)
    if user.zalo_id:
        await zalo.send_response(user.zalo_id, resp)
    if user.zalo_bot_id:
        await zalo_bot.send_response(user.zalo_bot_id, resp)
    if user.telegram_id:
        await telegram.send_response(user.telegram_id, resp)


async def morning_briefing(ctx: dict):
    """Generate and send morning briefing to all users with enabled trigger."""
    async with async_session() as db:
        triggers = await db.execute(
            select(ProactiveTrigger).where(
                ProactiveTrigger.trigger_type == "morning_briefing",
                ProactiveTrigger.enabled.is_(True),
            )
        )
        for trigger in triggers.scalars():
            try:
                user = await db.get(User, trigger.user_id)
                if not user:
                    continue

                uid = user.id
                today = datetime.utcnow().date()

                # Gather tasks
                tasks_q = await db.execute(
                    select(Task).where(Task.user_id == uid, Task.status != "done").order_by(Task.due_date).limit(5)
                )
                tasks = tasks_q.scalars().all()
                tasks_str = "\n".join(f"- [{t.priority}] {t.title}" for t in tasks) or "Không có task"

                # Gather events
                events_q = await db.execute(
                    select(CalendarEvent).where(
                        CalendarEvent.user_id == uid,
                        CalendarEvent.start_time >= datetime.combine(today, datetime.min.time()),
                        CalendarEvent.start_time < datetime.combine(today, datetime.max.time()),
                    )
                )
                events = events_q.scalars().all()
                events_str = "\n".join(f"- {e.start_time.strftime('%H:%M')} {e.title}" for e in events) or "Trống"

                # Generate briefing via cheap LLM
                llm = get_llm("gemini-2.0-flash")
                resp = await llm.ainvoke(BRIEFING_PROMPT.format(tasks=tasks_str, events=events_str))
                await _send_to_user(user, f"☀️ Chào buổi sáng!\n\n{resp.content}", "briefing")

                # Update last_fired
                trigger.last_fired = datetime.utcnow()
                await db.commit()
            except Exception:
                logger.exception(f"Briefing failed for user {trigger.user_id}")


async def deadline_reminders(ctx: dict):
    """Check for tasks due within 24h and send reminders."""
    async with async_session() as db:
        cutoff = datetime.utcnow() + timedelta(hours=24)
        tasks_q = await db.execute(
            select(Task).where(
                Task.status != "done",
                Task.due_date.isnot(None),
                Task.due_date <= cutoff,
                Task.due_date >= datetime.utcnow(),
            )
        )
        for task in tasks_q.scalars():
            try:
                user = await db.get(User, task.user_id)
                if user:
                    hours_left = (task.due_date - datetime.utcnow()).total_seconds() / 3600
                    await _send_to_user(user, f"⏰ Nhắc nhở: \"{task.title}\" còn {hours_left:.0f}h nữa là hết hạn!", "reminder")
            except Exception:
                logger.exception(f"Reminder failed for task {task.id}")


class WorkerSettings:
    """ARQ worker settings — referenced by docker-compose worker command."""
    from urllib.parse import urlparse as _urlparse
    _p = _urlparse(settings.REDIS_URL)
    redis_settings = RedisSettings(host=_p.hostname or "redis", port=_p.port or 6379, password=_p.password or None, database=int((_p.path or "/0").strip("/") or 0))
    cron_jobs = [
        cron(morning_briefing, hour=1, minute=0),   # 08:00 VN (UTC+7)
        cron(deadline_reminders, hour=7, minute=0),  # Check every 6h
        cron(deadline_reminders, hour=13, minute=0),
    ]
