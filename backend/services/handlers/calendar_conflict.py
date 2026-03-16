"""Calendar conflict trigger — detect overlapping events."""
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import CalendarEvent, ProactiveTrigger
from services.trigger_engine import TriggerHandler, register_handler


@register_handler
class CalendarConflictHandler(TriggerHandler):
    TRIGGER_TYPE = "calendar_conflict"
    LISTENS_TO = ["calendar.created", "calendar.updated"]

    async def should_fire(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> bool:
        event_id = event["payload"].get("event_id")
        if not event_id:
            return False
        cal_event = await db.get(CalendarEvent, UUID(event_id))
        if not cal_event or not cal_event.start_time:
            return False

        end_time = cal_event.end_time or cal_event.start_time
        conflicts = (await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == trigger.user_id,
                CalendarEvent.id != cal_event.id,
                CalendarEvent.start_time < end_time,
                # end_time of existing > start_time of new
                and_(
                    CalendarEvent.end_time.isnot(None),
                    CalendarEvent.end_time > cal_event.start_time,
                ) | and_(
                    CalendarEvent.end_time.is_(None),
                    CalendarEvent.start_time >= cal_event.start_time,
                    CalendarEvent.start_time < end_time,
                ),
            )
        )).scalars().all()
        return len(conflicts) > 0

    async def build_message(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> str:
        event_id = event["payload"].get("event_id")
        cal_event = await db.get(CalendarEvent, UUID(event_id))
        if not cal_event:
            return ""

        end_time = cal_event.end_time or cal_event.start_time
        conflicts = (await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.user_id == trigger.user_id,
                CalendarEvent.id != cal_event.id,
                CalendarEvent.start_time < end_time,
                and_(
                    CalendarEvent.end_time.isnot(None),
                    CalendarEvent.end_time > cal_event.start_time,
                ) | and_(
                    CalendarEvent.end_time.is_(None),
                    CalendarEvent.start_time >= cal_event.start_time,
                    CalendarEvent.start_time < end_time,
                ),
            )
        )).scalars().all()

        time_fmt = cal_event.start_time.strftime("%H:%M")
        conflict_names = ", ".join(f"\"{c.title}\"" for c in conflicts[:3])
        return (
            f"📅 Trùng lịch: \"{cal_event.title}\" lúc {time_fmt} "
            f"trùng với {conflict_names}. Bạn muốn điều chỉnh không?"
        )
