"""Proactive trigger settings — list + toggle."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import ProactiveTrigger

router = APIRouter()


@router.get("/proactive")
async def list_triggers(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(ProactiveTrigger).where(ProactiveTrigger.user_id == UUID(user_id)))).scalars().all()
    return [{"id": str(t.id), "trigger_type": t.trigger_type, "schedule": t.schedule, "enabled": t.enabled} for t in rows]


@router.patch("/proactive/{trigger_id}")
async def toggle_trigger(trigger_id: str, enabled: bool, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await db.execute(update(ProactiveTrigger).where(ProactiveTrigger.id == UUID(trigger_id), ProactiveTrigger.user_id == UUID(user_id)).values(enabled=enabled))
    await db.commit()
    return {"ok": True}
