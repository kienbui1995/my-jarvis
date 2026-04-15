"""M82: Proactive Pattern Detection — spending trends, health patterns → alerts."""
from datetime import date, timedelta


async def detect_patterns(user_id: str, db) -> list[str]:
    """Detect anomalies and trends across user data."""
    from sqlalchemy import select, func
    from db.models import Expense, HealthLog, Subscription
    from uuid import UUID

    uid = UUID(user_id)
    alerts = []

    # Spending spike: this week vs last week
    today = date.today()
    this_week = today - timedelta(days=7)
    last_week = today - timedelta(days=14)

    this_spend = (await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == uid, func.date(Expense.created_at) >= this_week
        )
    )).scalar() or 0
    last_spend = (await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == uid, func.date(Expense.created_at).between(last_week, this_week)
        )
    )).scalar() or 0

    if last_spend > 0 and this_spend > last_spend * 1.5:
        alerts.append(f"💸 Chi tiêu tuần này ({this_spend:,.0f}đ) tăng {((this_spend/last_spend)-1)*100:.0f}% so với tuần trước!")

    # Health streak break
    exercise_days = (await db.execute(
        select(func.count(func.distinct(HealthLog.log_date))).where(
            HealthLog.user_id == uid, HealthLog.metric == "exercise", HealthLog.log_date >= this_week
        )
    )).scalar() or 0
    if exercise_days < 2:
        alerts.append(f"🏃 Chỉ tập {exercise_days} ngày tuần này — cố gắng thêm nhé!")

    # Subscription cost warning
    sub_total = (await db.execute(
        select(func.sum(Subscription.amount)).where(Subscription.user_id == uid, Subscription.active.is_(True))
    )).scalar() or 0
    if sub_total > 1_000_000:
        alerts.append(f"📱 Tổng subscriptions: {sub_total:,.0f}đ/tháng — review xem có cần cắt không?")

    return alerts
