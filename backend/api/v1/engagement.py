"""Engagement API — habits, achievements, data export."""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from services.achievements import check_achievements
from services.data_export import export_user_data
from services.habits import check_in, create_habit, list_habits

router = APIRouter()


# ── Habits ──

class HabitCreate(BaseModel):
    name: str
    frequency: str = "daily"


@router.post("/habits")
async def create_habit_endpoint(
    body: HabitCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_habit(user_id, body.name, body.frequency, db)


@router.get("/habits")
async def list_habits_endpoint(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_habits(user_id, db)


@router.post("/habits/{habit_id}/check-in")
async def check_in_endpoint(
    habit_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await check_in(user_id, habit_id, db)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


# ── Achievements ──

@router.get("/achievements")
async def get_achievements(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return {"badges": await check_achievements(user_id, db)}


# ── Data Export ──

@router.get("/export")
async def export_data(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    data = await export_user_data(user_id, db)
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=jarvis-export.json"},
    )
