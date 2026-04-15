"""M80: Cross-domain Reasoning — connect signals across all modules."""
from datetime import date, timedelta


async def cross_domain_insights(user_id: str, db) -> list[str]:
    """Analyze patterns across finance, health, productivity, relationships."""
    from sqlalchemy import select, func
    from db.models import Expense, HealthLog, Task
    from uuid import UUID

    uid = UUID(user_id)
    week_ago = date.today() - timedelta(days=7)
    insights = []

    # Spending vs mood correlation
    mood_avg = (await db.execute(
        select(func.avg(HealthLog.value)).where(
            HealthLog.user_id == uid, HealthLog.metric == "mood", HealthLog.log_date >= week_ago
        )
    )).scalar()
    spend_total = (await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == uid, func.date(Expense.created_at) >= week_ago
        )
    )).scalar()

    if mood_avg and mood_avg < 5 and spend_total and spend_total > 0:
        insights.append(f"📊 Mood thấp (avg {mood_avg:.1f}/10) + chi tiêu {spend_total:,.0f}đ tuần này — stress spending?")

    # Sleep vs productivity
    sleep_avg = (await db.execute(
        select(func.avg(HealthLog.value)).where(
            HealthLog.user_id == uid, HealthLog.metric == "sleep", HealthLog.log_date >= week_ago
        )
    )).scalar()
    tasks_done = (await db.execute(
        select(func.count()).where(
            Task.user_id == uid, Task.status == "done", func.date(Task.updated_at) >= week_ago
        )
    )).scalar() or 0

    if sleep_avg and sleep_avg < 6:
        insights.append(f"😴 Ngủ ít (avg {sleep_avg:.1f}h) — hoàn thành {tasks_done} tasks. Ngủ thêm có thể tăng năng suất.")
    elif sleep_avg and sleep_avg >= 7 and tasks_done > 10:
        insights.append(f"🌟 Ngủ đủ ({sleep_avg:.1f}h) + {tasks_done} tasks done — tuần hiệu quả!")

    return insights
