"""Budget exceeded trigger — alert when daily spending exceeds threshold."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Expense, ProactiveTrigger
from services.trigger_engine import TriggerHandler, register_handler

DEFAULT_DAILY_LIMIT = 500_000  # VND


@register_handler
class BudgetHandler(TriggerHandler):
    TRIGGER_TYPE = "budget_exceeded"
    LISTENS_TO = ["expense.created"]

    async def should_fire(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> bool:
        limit = (trigger.config or {}).get("daily_limit", DEFAULT_DAILY_LIMIT)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        total = (await db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.user_id == trigger.user_id,
                Expense.created_at >= today_start,
            )
        )).scalar()
        return total >= limit

    async def build_message(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> str:
        limit = (trigger.config or {}).get("daily_limit", DEFAULT_DAILY_LIMIT)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        total = (await db.execute(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.user_id == trigger.user_id,
                Expense.created_at >= today_start,
            )
        )).scalar()
        return (
            f"💰 Cảnh báo chi tiêu: Hôm nay bạn đã chi {total:,.0f} VND, "
            f"vượt ngưỡng {limit:,.0f} VND!"
        )
