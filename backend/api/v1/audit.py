"""M9 Audit trail API — query evidence logs."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models.evidence import EvidenceLog

router = APIRouter()


@router.get("/")
async def list_evidence(
    conversation_id: str | None = None,
    event_type: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    uid = UUID(user_id)
    q = select(EvidenceLog).where(EvidenceLog.user_id == uid)
    if conversation_id:
        q = q.where(EvidenceLog.conversation_id == UUID(conversation_id))
    if event_type:
        q = q.where(EvidenceLog.event_type == event_type)
    q = q.order_by(EvidenceLog.timestamp.desc()).offset(offset).limit(limit)

    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "id": str(r.id), "timestamp": r.timestamp.isoformat(), "node": r.node,
            "event_type": r.event_type, "tool_name": r.tool_name,
            "duration_ms": r.duration_ms, "error": r.error or None,
        }
        for r in rows
    ]
