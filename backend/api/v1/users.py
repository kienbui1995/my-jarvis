"""User profile endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel

from core.deps import get_db, get_current_user_id
from db.models import User

router = APIRouter()


async def _get_user(user_id: str, db: AsyncSession) -> User:
    user = await db.get(User, UUID(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me")
async def get_profile(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await _get_user(user_id, db)
    return {"id": str(user.id), "name": user.name, "email": user.email, "tier": user.tier, "timezone": user.timezone}


class ProfileUpdate(BaseModel):
    name: str | None = None
    timezone: str | None = None
    preferences: dict | None = None


@router.patch("/me")
async def update_profile(body: ProfileUpdate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await _get_user(user_id, db)
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(user, field, val)
    await db.commit()
    return {"ok": True}


@router.get("/me/connections")
async def get_connections(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Return which channels are linked to this user."""
    user = await _get_user(user_id, db)
    from core.config import settings
    return {
        "connections": [
            {"channel": "telegram", "connected": bool(user.telegram_id), "bot_username": settings.TELEGRAM_BOT_USERNAME or None},
            {"channel": "zalo_oa", "connected": bool(user.zalo_id), "oa_id": settings.ZALO_OA_ID or None},
            {"channel": "zalo_bot", "connected": bool(user.zalo_bot_id)},
        ]
    }


@router.post("/me/connections/link")
async def create_link_code(user_id: str = Depends(get_current_user_id)):
    """Generate a 6-digit code for linking a channel account to this web user."""
    import secrets
    from llm.budget import get_redis
    redis = await get_redis()
    code = f"{secrets.randbelow(900000) + 100000}"
    await redis.set(f"link:{code}", user_id, ex=300)  # 5 min TTL
    return {"code": code, "expires_in": 300}


@router.post("/me/connections/unlink")
async def unlink_channel(channel: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Unlink a channel from this user."""
    user = await _get_user(user_id, db)
    field = {"telegram": "telegram_id", "zalo_oa": "zalo_id", "zalo_bot": "zalo_bot_id"}.get(channel)
    if not field:
        raise HTTPException(status_code=400, detail="Invalid channel")
    setattr(user, field, None)
    await db.commit()
    return {"ok": True}
