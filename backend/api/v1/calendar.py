"""Calendar endpoints for web dashboard."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import CalendarEvent
from services.event_bus import emit

router = APIRouter()


class EventCreate(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime | None = None
    location: str = ""


@router.get("/")
async def list_events(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CalendarEvent).where(CalendarEvent.user_id == UUID(user_id)).order_by(CalendarEvent.start_time).limit(50)
    )
    return [{"id": str(e.id), "title": e.title, "start_time": e.start_time.isoformat(), "location": e.location} for e in result.scalars()]


@router.post("/")
async def create_event(req: EventCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    event = CalendarEvent(user_id=UUID(user_id), title=req.title, start_time=req.start_time, end_time=req.end_time, location=req.location)
    db.add(event)
    await db.commit()
    await emit("calendar.created", user_id, {"event_id": str(event.id), "title": event.title})
    return {"id": str(event.id), "title": event.title}
