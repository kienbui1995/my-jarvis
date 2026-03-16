"""M43 Achievements — gamification badges and milestones."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import LLMUsage, Task
from db.models.system import Habit

BADGES = [
    {"id": "first_chat", "name": "Bước đầu",
     "desc": "Gửi tin nhắn đầu tiên", "check": "messages >= 1"},
    {"id": "streak_7", "name": "7 ngày liền",
     "desc": "Duy trì habit 7 ngày", "check": "streak >= 7"},
    {"id": "streak_30", "name": "Kiên trì",
     "desc": "Duy trì habit 30 ngày", "check": "streak >= 30"},
    {"id": "task_master", "name": "Task Master",
     "desc": "Hoàn thành 50 tasks", "check": "done_tasks >= 50"},
    {"id": "power_user", "name": "Power User",
     "desc": "100 tin nhắn", "check": "messages >= 100"},
    {"id": "explorer", "name": "Khám phá",
     "desc": "Dùng 10 tools khác nhau", "check": "tools >= 10"},
]


async def check_achievements(user_id: str, db: AsyncSession) -> list[dict]:
    """Check which badges user has earned."""
    uid = UUID(user_id)
    earned = []

    # Count messages
    msg_count = (await db.execute(
        select(func.count()).where(LLMUsage.user_id == uid)
    )).scalar() or 0

    # Count done tasks
    done_tasks = (await db.execute(
        select(func.count()).where(Task.user_id == uid, Task.status == "done")
    )).scalar() or 0

    # Best streak
    best_streak = (await db.execute(
        select(func.max(Habit.best_streak)).where(Habit.user_id == uid)
    )).scalar() or 0

    # Distinct tools used
    tool_count = (await db.execute(
        select(func.count(func.distinct(LLMUsage.task_type))).where(
            LLMUsage.user_id == uid, LLMUsage.task_type.isnot(None),
        )
    )).scalar() or 0

    stats = {
        "messages": msg_count, "done_tasks": done_tasks,
        "streak": best_streak, "tools": tool_count,
    }

    for badge in BADGES:
        check = badge["check"]
        # Simple eval: "messages >= 100"
        field, op, val = check.split()
        actual = stats.get(field, 0)
        if op == ">=" and actual >= int(val):
            earned.append({"id": badge["id"], "name": badge["name"], "desc": badge["desc"]})

    return earned
