"""M91: Push notification token registration."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.deps import get_current_user_id, get_db
from services.push import PushToken

router = APIRouter()


class TokenRegister(BaseModel):
    token: str
    platform: str = "expo"


@router.post("/register")
async def register_push_token(body: TokenRegister, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    existing = (await db.execute(
        select(PushToken).where(PushToken.token == body.token)
    )).scalar_one_or_none()
    if existing:
        existing.user_id = uid
    else:
        db.add(PushToken(user_id=uid, token=body.token, platform=body.platform))
    await db.commit()
    return {"ok": True}
