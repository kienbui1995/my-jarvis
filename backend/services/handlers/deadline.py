"""Deadline approaching trigger — notify when task is due within N hours."""
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ProactiveTrigger, Task
from services.trigger_engine import TriggerHandler, register_handler

DEFAULT_HOURS_BEFORE = 2


@register_handler
class DeadlineHandler(TriggerHandler):
    TRIGGER_TYPE = "deadline_approaching"
    LISTENS_TO = ["task.created", "task.updated", "cron.check_deadlines"]

    async def should_fire(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> bool:
        hours = (trigger.config or {}).get("hours_before", DEFAULT_HOURS_BEFORE)
        cutoff = datetime.utcnow() + timedelta(hours=hours)

        if event["type"] in ("task.created", "task.updated"):
            task_id = event["payload"].get("task_id")
            if not task_id:
                return False
            task = await db.get(Task, UUID(task_id))
            return bool(
                task and task.due_date and task.due_date <= cutoff and task.status != "done"
            )

        # cron.check_deadlines — check all tasks for this user
        return True

    async def build_message(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> str:
        hours = (trigger.config or {}).get("hours_before", DEFAULT_HOURS_BEFORE)
        cutoff = datetime.utcnow() + timedelta(hours=hours)

        if event["type"] in ("task.created", "task.updated"):
            task_id = event["payload"].get("task_id")
            task = await db.get(Task, UUID(task_id))
            if not task or not task.due_date:
                return ""
            hrs = max(0, (task.due_date - datetime.utcnow()).total_seconds() / 3600)
            return f"⏰ Nhắc nhở: \"{task.title}\" còn {hrs:.0f}h nữa là hết hạn!"

        # cron — batch check
        tasks = (await db.execute(
            select(Task).where(
                Task.user_id == trigger.user_id,
                Task.status != "done",
                Task.due_date.isnot(None),
                Task.due_date <= cutoff,
                Task.due_date >= datetime.utcnow(),
            )
        )).scalars().all()
        if not tasks:
            return ""
        lines = [f"⏰ {len(tasks)} task sắp hết hạn:"]
        for t in tasks:
            hrs = max(0, (t.due_date - datetime.utcnow()).total_seconds() / 3600)
            lines.append(f"  - \"{t.title}\" (còn {hrs:.0f}h)")
        return "\n".join(lines)
