"""M79: Context Awareness — infer user's current context from signals."""
from datetime import datetime


async def get_user_context(user_id: str, db) -> dict:
    """Build current context from calendar, health, location, time."""
    from sqlalchemy import select, func
    from db.models import CalendarEvent, HealthLog
    from uuid import UUID

    now = datetime.now()
    uid = UUID(user_id)
    ctx = {"time": now.isoformat(), "period": _time_period(now.hour), "day": now.strftime("%A")}

    # Current/next calendar event
    event = (await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.user_id == uid,
            CalendarEvent.start_time <= now,
            CalendarEvent.end_time >= now,
        ).limit(1)
    )).scalar_one_or_none()
    if event:
        ctx["current_activity"] = event.title

    next_event = (await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.user_id == uid,
            CalendarEvent.start_time > now,
        ).order_by(CalendarEvent.start_time).limit(1)
    )).scalar_one_or_none()
    if next_event:
        ctx["next_event"] = {"title": next_event.title, "starts": next_event.start_time.isoformat()}

    # Today's mood (latest)
    mood = (await db.execute(
        select(HealthLog.value).where(
            HealthLog.user_id == uid, HealthLog.metric == "mood",
            HealthLog.log_date == now.date(),
        ).order_by(HealthLog.created_at.desc()).limit(1)
    )).scalar_one_or_none()
    if mood:
        ctx["mood"] = mood

    return ctx


def _time_period(hour: int) -> str:
    if hour < 6: return "night"
    if hour < 12: return "morning"
    if hour < 14: return "lunch"
    if hour < 18: return "afternoon"
    if hour < 22: return "evening"
    return "night"
