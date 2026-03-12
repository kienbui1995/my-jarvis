"""M11 Tool Permissions + M5 Preferences API."""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.tools import all_tools
from core.deps import get_current_user_id, get_db
from db.models.preference import UserPreference, UserToolPermission

router = APIRouter()


# ── M5: Preferences ──────────────────────────────────────────

@router.get("/preferences")
async def get_preferences(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    pref = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == UUID(user_id))
    )).scalar_one_or_none()
    if not pref:
        return {"tone": None, "verbosity": None, "language": None, "interests": []}
    return {"tone": pref.tone, "verbosity": pref.verbosity, "language": pref.language, "interests": pref.interests or []}


class PrefUpdate(BaseModel):
    tone: str | None = None
    verbosity: str | None = None
    language: str | None = None
    interests: list[str] | None = None


@router.patch("/preferences")
async def update_preferences(body: PrefUpdate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    pref = (await db.execute(select(UserPreference).where(UserPreference.user_id == uid))).scalar_one_or_none()
    if not pref:
        pref = UserPreference(user_id=uid)
        db.add(pref)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(pref, k, v)
    await db.commit()
    return {"ok": True}


# ── M11: Tool Permissions ────────────────────────────────────

@router.get("/tools")
async def list_tool_permissions(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    perms = {p.tool_name: p for p in (await db.execute(
        select(UserToolPermission).where(UserToolPermission.user_id == uid)
    )).scalars().all()}

    return [
        {
            "tool_name": t.name,
            "description": t.description or "",
            "enabled": perms[t.name].enabled if t.name in perms else True,
            "requires_approval": perms[t.name].requires_approval if t.name in perms else False,
        }
        for t in all_tools
    ]


class ToolPermUpdate(BaseModel):
    enabled: bool | None = None
    requires_approval: bool | None = None


@router.patch("/tools/{tool_name}")
async def update_tool_permission(tool_name: str, body: ToolPermUpdate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    perm = (await db.execute(
        select(UserToolPermission).where(UserToolPermission.user_id == uid, UserToolPermission.tool_name == tool_name)
    )).scalar_one_or_none()
    if not perm:
        perm = UserToolPermission(user_id=uid, tool_name=tool_name)
        db.add(perm)
    if body.enabled is not None:
        perm.enabled = body.enabled
    if body.requires_approval is not None:
        perm.requires_approval = body.requires_approval
    await db.commit()
    return {"ok": True}
