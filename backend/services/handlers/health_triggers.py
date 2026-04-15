"""V11: Health triggers — medication, daily reflection, meditation, screen break."""
from datetime import date, datetime

from sqlalchemy import select

from db.models import Medication
from services.trigger_engine import TriggerHandler, register_handler


@register_handler
class MedicationDueHandler(TriggerHandler):
    TRIGGER_TYPE = "medication_due"
    LISTENS_TO = ["cron.morning_briefing", "cron.evening_briefing"]

    async def should_fire(self, trigger, event, db) -> bool:
        now = datetime.now().strftime("%H:%M")
        self._meds = (await db.execute(
            select(Medication).where(
                Medication.user_id == trigger.user_id,
                Medication.active.is_(True),
            )
        )).scalars().all()
        # Filter meds that have a time matching current hour
        hour = datetime.now().hour
        self._due = [m for m in self._meds if any(t.startswith(f"{hour:02d}:") for t in (m.times or []))]
        return len(self._due) > 0

    async def build_message(self, trigger, event, db) -> str:
        lines = ["💊 Nhắc uống thuốc:"]
        for m in self._due:
            lines.append(f"  • {m.name}{f' — {m.dosage}' if m.dosage else ''}")
        return "\n".join(lines)


@register_handler
class DailyReflectionHandler(TriggerHandler):
    TRIGGER_TYPE = "daily_reflection"
    LISTENS_TO = ["cron.evening_briefing"]

    async def should_fire(self, trigger, event, db) -> bool:
        return True  # Always fire in evening

    async def build_message(self, trigger, event, db) -> str:
        return "🌙 Cuối ngày rồi! Hôm nay bạn thế nào?\n\n• Mood (1-10)?\n• Điều tốt nhất hôm nay?\n• Ngày mai muốn làm gì?"


@register_handler
class ScreenBreakHandler(TriggerHandler):
    TRIGGER_TYPE = "screen_break"
    LISTENS_TO = ["cron.hourly"]

    async def should_fire(self, trigger, event, db) -> bool:
        hour = datetime.now().hour
        return 9 <= hour <= 22  # Only during waking hours

    async def build_message(self, trigger, event, db) -> str:
        return "👀 Nghỉ mắt 20 giây — nhìn xa 20 feet! Đứng dậy vươn vai 💪"
