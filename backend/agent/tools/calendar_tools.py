"""Calendar tools — wired to DB, user_id injected from InjectedToolArg."""
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from langchain_core.tools import tool, InjectedToolArg
from sqlalchemy import select

from db.models import CalendarEvent
from db.session import async_session


@tool
async def calendar_create(
    title: str, start_time: str, end_time: str = "", location: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Tạo sự kiện lịch. Args: title, start_time (ISO), end_time (ISO, optional), location (optional)."""
    async with async_session() as db:
        e = CalendarEvent(
            user_id=UUID(user_id), title=title,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time) if end_time else None,
            location=location or None,
        )
        db.add(e)
        await db.commit()
        return f"📅 Đã tạo sự kiện: {title} lúc {start_time}"


@tool
async def calendar_list(
    days: int = 7,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Xem lịch sắp tới. Args: days (số ngày, mặc định 7)."""
    now = datetime.utcnow()
    async with async_session() as db:
        result = await db.execute(
            select(CalendarEvent)
            .where(CalendarEvent.user_id == UUID(user_id), CalendarEvent.start_time >= now, CalendarEvent.start_time <= now + timedelta(days=days))
            .order_by(CalendarEvent.start_time)
            .limit(10)
        )
        events = result.scalars().all()
        if not events:
            return "📅 Không có sự kiện nào trong thời gian tới."
        return "\n".join(f"- {e.start_time.strftime('%d/%m %H:%M')} {e.title}" + (f" @ {e.location}" if e.location else "") for e in events)
