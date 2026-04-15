"""M53+M56: Bill due + Birthday reminder trigger handlers."""
from datetime import date

from sqlalchemy import select

from db.models import BillReminder, Contact
from services.trigger_engine import TriggerHandler, register_handler


@register_handler
class BillDueHandler(TriggerHandler):
    TRIGGER_TYPE = "bill_due"
    LISTENS_TO = ["cron.morning_briefing"]

    async def should_fire(self, trigger, event, db) -> bool:
        today = date.today().day
        bills = (await db.execute(
            select(BillReminder).where(
                BillReminder.user_id == trigger.user_id,
                BillReminder.enabled.is_(True),
                BillReminder.due_day == today,
            )
        )).scalars().all()
        self._bills = bills
        return len(bills) > 0

    async def build_message(self, trigger, event, db) -> str:
        lines = ["💰 Hôm nay có hóa đơn cần thanh toán:"]
        for b in self._bills:
            amt = f" — {b.amount:,.0f} {b.currency}" if b.amount else ""
            lines.append(f"  • {b.name}{amt}")
        return "\n".join(lines)


@register_handler
class BirthdayReminderHandler(TriggerHandler):
    TRIGGER_TYPE = "birthday_reminder"
    LISTENS_TO = ["cron.morning_briefing"]

    async def should_fire(self, trigger, event, db) -> bool:
        today = date.today()
        from sqlalchemy import func as sa_func
        self._birthdays = (await db.execute(
            select(Contact).where(
                Contact.user_id == trigger.user_id,
                Contact.birthday.isnot(None),
                sa_func.extract("month", Contact.birthday) == today.month,
                sa_func.extract("day", Contact.birthday) == today.day,
            )
        )).scalars().all()
        return len(self._birthdays) > 0

    async def build_message(self, trigger, event, db) -> str:
        lines = ["🎂 Sinh nhật hôm nay:"]
        for c in self._birthdays:
            prefs = c.preferences or {}
            gift_hint = f" (gợi ý: {prefs.get('gift_ideas', 'chưa có')})" if prefs.get("gift_ideas") else ""
            lines.append(f"  • {c.name} ({c.relationship or '?'}){gift_hint}")
        return "\n".join(lines)
