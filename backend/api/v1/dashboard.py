"""M83: Life Dashboard + M86: Goals + M87: Decisions APIs."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.deps import get_current_user_id, get_db
from core.pagination import PaginationParams, paginated_response
from db.models import Decision, Expense, Goal, HealthLog, Task
from services.crud import CRUDService

router = APIRouter()
goal_svc = CRUDService(Goal)
decision_svc = CRUDService(Decision)


# ── Life Dashboard (M83) ──

@router.get("/overview")
async def life_overview(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    week_ago = date.today() - timedelta(days=7)

    tasks_done = (await db.execute(
        select(func.count()).where(Task.user_id == uid, Task.status == "done", func.date(Task.updated_at) >= week_ago)
    )).scalar() or 0

    spend_week = (await db.execute(
        select(func.sum(Expense.amount)).where(Expense.user_id == uid, func.date(Expense.created_at) >= week_ago)
    )).scalar() or 0

    mood_avg = (await db.execute(
        select(func.avg(HealthLog.value)).where(HealthLog.user_id == uid, HealthLog.metric == "mood", HealthLog.log_date >= week_ago)
    )).scalar()

    active_goals = (await db.execute(
        select(func.count()).where(Goal.user_id == uid, Goal.status == "active")
    )).scalar() or 0

    return {
        "week": {
            "tasks_completed": tasks_done,
            "spending": float(spend_week),
            "mood_avg": round(mood_avg, 1) if mood_avg else None,
            "active_goals": active_goals,
        }
    }


# ── Goals (M86) ──

class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    goal_type: str = "objective"
    parent_id: str | None = None
    target_value: float | None = None
    unit: str | None = None
    deadline: date | None = None


@router.get("/goals")
async def list_goals(status: str = "active", p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await goal_svc.list(db, user_id, page=p.page, page_size=p.page_size, filters={"status": status})
    return paginated_response(items, total, p)


@router.post("/goals")
async def create_goal(body: GoalCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await goal_svc.create(db, user_id, **body.model_dump(exclude_none=True))


@router.patch("/goals/{goal_id}")
async def update_goal(goal_id: str, body: dict, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await goal_svc.update(db, user_id, goal_id, **body)


# ── Decisions (M87) ──

class DecisionCreate(BaseModel):
    title: str
    context: str | None = None
    options: list[dict] = []
    chosen: str | None = None
    reasoning: str | None = None
    review_date: date | None = None


@router.get("/decisions")
async def list_decisions(p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await decision_svc.list(db, user_id, page=p.page, page_size=p.page_size)
    return paginated_response(items, total, p)


@router.post("/decisions")
async def create_decision(body: DecisionCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await decision_svc.create(db, user_id, **body.model_dump(exclude_none=True))


@router.patch("/decisions/{decision_id}")
async def update_decision(decision_id: str, body: dict, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await decision_svc.update(db, user_id, decision_id, **body)
