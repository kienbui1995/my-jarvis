"""M41 Daily Habits — habit tracker with streaks."""
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.system import Habit, HabitLog


async def create_habit(
    user_id: str, name: str, frequency: str, db: AsyncSession,
) -> dict:
    h = Habit(user_id=UUID(user_id), name=name, frequency=frequency)
    db.add(h)
    await db.commit()
    return {"id": str(h.id), "name": h.name}


async def check_in(user_id: str, habit_id: str, db: AsyncSession) -> dict:
    """Record a habit check-in and update streak."""
    h = await db.get(Habit, UUID(habit_id))
    if not h or str(h.user_id) != user_id:
        return {"error": "Habit not found"}

    today = datetime.utcnow().date()
    # Check if already checked in today
    existing = (await db.execute(
        select(HabitLog).where(
            HabitLog.habit_id == h.id,
            func.date(HabitLog.checked_at) == today,
        )
    )).scalar_one_or_none()
    if existing:
        return {"streak": h.streak, "message": "Đã check-in hôm nay rồi!"}

    db.add(HabitLog(habit_id=h.id))

    # Update streak
    yesterday = today - timedelta(days=1)
    yesterday_log = (await db.execute(
        select(HabitLog).where(
            HabitLog.habit_id == h.id,
            func.date(HabitLog.checked_at) == yesterday,
        )
    )).scalar_one_or_none()

    if yesterday_log:
        h.streak = (h.streak or 0) + 1
    else:
        h.streak = 1
    if h.streak > (h.best_streak or 0):
        h.best_streak = h.streak

    await db.commit()
    return {"streak": h.streak, "best": h.best_streak}


async def list_habits(user_id: str, db: AsyncSession) -> list[dict]:
    rows = (await db.execute(
        select(Habit).where(Habit.user_id == UUID(user_id))
    )).scalars().all()
    return [
        {"id": str(h.id), "name": h.name, "streak": h.streak or 0,
         "best_streak": h.best_streak or 0, "frequency": h.frequency}
        for h in rows
    ]
