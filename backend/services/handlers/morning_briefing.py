"""Morning briefing trigger — daily summary via LLM (migrated from V3 cron)."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CalendarEvent, ProactiveTrigger, Task
from llm.gateway import get_llm
from services.trigger_engine import TriggerHandler, register_handler

BRIEFING_PROMPT = """Tạo bản tóm tắt buổi sáng ngắn gọn (tối đa 150 từ) bằng tiếng Việt cho user.

Tasks hôm nay:
{tasks}

Lịch hôm nay:
{events}

Phong cách: thân thiện, động viên, đi thẳng vào trọng tâm."""


@register_handler
class MorningBriefingHandler(TriggerHandler):
    TRIGGER_TYPE = "morning_briefing"
    LISTENS_TO = ["cron.morning_briefing"]

    async def should_fire(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> bool:
        # Always fire for cron event — the cron itself is the schedule gate
        return True

    async def build_message(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> str:
        uid = trigger.user_id
        today = datetime.utcnow().date()

        tasks = (await db.execute(
            select(Task).where(
                Task.user_id == uid, Task.status != "done"
            ).order_by(Task.due_date).limit(5)
        )).scalars().all()
        tasks_str = "\n".join(f"- [{t.priority}] {t.title}" for t in tasks) or "Không có task"

        events = (await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == uid,
                CalendarEvent.start_time >= datetime.combine(today, datetime.min.time()),
                CalendarEvent.start_time < datetime.combine(today, datetime.max.time()),
            )
        )).scalars().all()
        events_str = (
            "\n".join(f"- {e.start_time.strftime('%H:%M')} {e.title}" for e in events)
            or "Trống"
        )

        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(BRIEFING_PROMPT.format(tasks=tasks_str, events=events_str))
        return f"☀️ Chào buổi sáng!\n\n{resp.content}"
