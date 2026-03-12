"""Analytics endpoints — usage stats, spending."""
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import LLMUsage, Expense

router = APIRouter()


@router.get("/usage")
async def get_usage(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    row = (await db.execute(
        select(
            func.count().label("messages"),
            func.coalesce(func.sum(LLMUsage.input_tokens + LLMUsage.output_tokens), 0).label("tokens"),
            func.coalesce(func.sum(LLMUsage.cost), 0).label("cost"),
        ).where(LLMUsage.user_id == uid, LLMUsage.created_at >= today)
    )).one()
    return {"messages_today": row.messages, "tokens_today": int(row.tokens), "cost_today": round(float(row.cost), 4)}


@router.get("/spending")
async def get_spending(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rows = (await db.execute(
        select(Expense.category, func.sum(Expense.amount).label("total"))
        .where(Expense.user_id == uid, Expense.created_at >= month_start)
        .group_by(Expense.category)
    )).all()
    by_cat = {r.category: float(r.total) for r in rows}
    return {"total_this_month": sum(by_cat.values()), "by_category": by_cat}


@router.get("/weekly")
async def get_weekly(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    week_ago = datetime.utcnow() - timedelta(days=7)
    rows = (await db.execute(
        select(
            cast(LLMUsage.created_at, Date).label("date"),
            func.count().label("messages"),
            func.coalesce(func.sum(LLMUsage.cost), 0).label("cost"),
        ).where(LLMUsage.user_id == uid, LLMUsage.created_at >= week_ago)
        .group_by(cast(LLMUsage.created_at, Date))
        .order_by(cast(LLMUsage.created_at, Date))
    )).all()
    return [{"date": r.date.isoformat(), "messages": r.messages, "cost": round(float(r.cost), 4)} for r in rows]
