"""Notifications API — list + mark read."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import Notification

router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    q = select(Notification).where(Notification.user_id == UUID(user_id))
    if unread_only:
        q = q.where(Notification.read.is_(False))
    q = q.order_by(Notification.created_at.desc()).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [
        {"id": str(n.id), "type": n.type, "content": n.content, "read": n.read, "created_at": n.created_at.isoformat()}
        for n in rows
    ]


@router.patch("/notifications/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == UUID(user_id))
        .values(read=True)
    )
    await db.commit()
    return {"ok": True}
