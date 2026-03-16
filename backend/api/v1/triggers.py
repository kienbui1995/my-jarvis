"""Trigger CRUD API — create, list, update, delete proactive triggers."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import ProactiveTrigger
from services.trigger_engine import get_all_trigger_types

router = APIRouter()


class TriggerCreate(BaseModel):
    trigger_type: str
    config: dict | None = None
    enabled: bool = True


class TriggerUpdate(BaseModel):
    config: dict | None = None
    enabled: bool | None = None


@router.get("/")
async def list_triggers(
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(ProactiveTrigger).where(ProactiveTrigger.user_id == UUID(user_id))
    )).scalars().all()
    return [
        {
            "id": str(t.id), "trigger_type": t.trigger_type,
            "config": t.config, "enabled": t.enabled,
            "last_fired": t.last_fired.isoformat() if t.last_fired else None,
        }
        for t in rows
    ]


@router.get("/types")
async def list_trigger_types():
    """List all available trigger types that can be created."""
    return {"types": get_all_trigger_types()}


@router.post("/")
async def create_trigger(
    body: TriggerCreate,
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db),
):
    if body.trigger_type not in get_all_trigger_types():
        raise HTTPException(400, f"Unknown trigger type: {body.trigger_type}")
    # Check for duplicate
    existing = (await db.execute(
        select(ProactiveTrigger).where(
            ProactiveTrigger.user_id == UUID(user_id),
            ProactiveTrigger.trigger_type == body.trigger_type,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(409, f"Trigger '{body.trigger_type}' already exists for this user")
    trigger = ProactiveTrigger(
        user_id=UUID(user_id),
        trigger_type=body.trigger_type,
        config=body.config,
        enabled=body.enabled,
    )
    db.add(trigger)
    await db.commit()
    return {"id": str(trigger.id), "trigger_type": trigger.trigger_type}


@router.patch("/{trigger_id}")
async def update_trigger(
    trigger_id: str, body: TriggerUpdate,
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db),
):
    trigger = (await db.execute(
        select(ProactiveTrigger).where(
            ProactiveTrigger.id == UUID(trigger_id),
            ProactiveTrigger.user_id == UUID(user_id),
        )
    )).scalar_one_or_none()
    if not trigger:
        raise HTTPException(404, "Trigger not found")
    if body.config is not None:
        trigger.config = body.config
    if body.enabled is not None:
        trigger.enabled = body.enabled
    await db.commit()
    return {"ok": True}


@router.delete("/{trigger_id}")
async def delete_trigger(
    trigger_id: str,
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db),
):
    await db.execute(sql_delete(ProactiveTrigger).where(
        ProactiveTrigger.id == UUID(trigger_id),
        ProactiveTrigger.user_id == UUID(user_id),
    ))
    await db.commit()
    return {"ok": True}
