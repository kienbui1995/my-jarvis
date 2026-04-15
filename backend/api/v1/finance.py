"""M52: Financial Dashboard + M53: Bill Reminders + M54: Subscription Tracker."""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from core.pagination import PaginationParams, paginated_response
from db.models import BillReminder, Expense, Subscription
from services.crud import CRUDService
from uuid import UUID

router = APIRouter()
bill_svc = CRUDService(BillReminder)
sub_svc = CRUDService(Subscription)


# ── Dashboard (M52) ──

@router.get("/dashboard")
async def financial_dashboard(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    # Monthly spending
    month_total = (await db.execute(
        select(func.sum(Expense.amount)).where(
            Expense.user_id == uid,
            func.date_trunc("month", Expense.created_at) == func.date_trunc("month", func.now()),
        )
    )).scalar() or 0

    # By category
    categories = (await db.execute(
        select(Expense.category, func.sum(Expense.amount)).where(
            Expense.user_id == uid,
            func.date_trunc("month", Expense.created_at) == func.date_trunc("month", func.now()),
        ).group_by(Expense.category)
    )).all()

    # Active subscriptions total
    sub_total = (await db.execute(
        select(func.sum(Subscription.amount)).where(Subscription.user_id == uid, Subscription.active.is_(True))
    )).scalar() or 0

    return {
        "month_total": float(month_total),
        "by_category": {c: float(a) for c, a in categories},
        "subscriptions_monthly": float(sub_total),
    }


# ── Bills (M53) ──

class BillCreate(BaseModel):
    name: str
    amount: float | None = None
    due_day: int = 1
    frequency: str = "monthly"
    category: str = "utilities"


@router.get("/bills")
async def list_bills(p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await bill_svc.list(db, user_id, page=p.page, page_size=p.page_size)
    return paginated_response(items, total, p)


@router.post("/bills")
async def create_bill(body: BillCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await bill_svc.create(db, user_id, **body.model_dump())


@router.delete("/bills/{bill_id}")
async def delete_bill(bill_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await bill_svc.delete(db, user_id, bill_id)
    return {"ok": True}


# ── Subscriptions (M54) ──

class SubCreate(BaseModel):
    name: str
    amount: float
    frequency: str = "monthly"
    category: str = "entertainment"
    next_billing: date | None = None


@router.get("/subscriptions")
async def list_subs(p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await sub_svc.list(db, user_id, page=p.page, page_size=p.page_size)
    return paginated_response(items, total, p)


@router.post("/subscriptions")
async def create_sub(body: SubCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await sub_svc.create(db, user_id, **body.model_dump())


@router.delete("/subscriptions/{sub_id}")
async def delete_sub(sub_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await sub_svc.delete(db, user_id, sub_id)
    return {"ok": True}
