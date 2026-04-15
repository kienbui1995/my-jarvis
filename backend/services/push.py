"""M91: Push notification service + token model."""
import logging
from datetime import datetime

import httpx
from sqlalchemy import String, DateTime, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, UserOwnedMixin

logger = logging.getLogger(__name__)


class PushToken(UserOwnedMixin, Base):
    __tablename__ = "push_tokens"

    token: Mapped[str] = mapped_column(String(500), unique=True)
    platform: Mapped[str] = mapped_column(String(20), default="expo")  # expo, fcm, apns
    last_used: Mapped[datetime | None] = mapped_column(DateTime)


async def send_push(user_id: str, title: str, body: str, db: AsyncSession):
    """Send push notification to all user's registered devices."""
    from uuid import UUID as _UUID
    tokens = (await db.execute(
        select(PushToken).where(PushToken.user_id == _UUID(user_id))
    )).scalars().all()

    if not tokens:
        return

    async with httpx.AsyncClient() as client:
        for t in tokens:
            if t.platform == "expo":
                await client.post("https://exp.host/--/api/v2/push/send", json={
                    "to": t.token, "title": title, "body": body, "sound": "default",
                })
            t.last_used = datetime.utcnow()
        await db.commit()
