"""Conversation management — list, create, get messages."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import Conversation, Message

router = APIRouter()


@router.get("/")
async def list_conversations(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    uid = UUID(user_id)
    subq = select(Message.conversation_id, func.count().label("cnt")).group_by(Message.conversation_id).subquery()
    rows = (await db.execute(
        select(Conversation, func.coalesce(subq.c.cnt, 0).label("message_count"))
        .outerjoin(subq, Conversation.id == subq.c.conversation_id)
        .where(Conversation.user_id == uid, Conversation.channel == "web")
        .order_by(Conversation.started_at.desc()).limit(50)
    )).all()
    return [{"id": str(c.id), "channel": c.channel, "summary": c.summary or c.rolling_summary, "started_at": c.started_at.isoformat(), "message_count": cnt, "total_turns": c.total_turns} for c, cnt in rows]


@router.post("/")
async def create_conversation(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    conv = Conversation(user_id=UUID(user_id), channel="web")
    db.add(conv)
    await db.commit()
    return {"id": str(conv.id)}


@router.get("/{conv_id}/messages")
async def get_messages(conv_id: str, limit: int = 50, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(Message).join(Conversation).where(
            Message.conversation_id == UUID(conv_id), Conversation.user_id == UUID(user_id)
        ).order_by(Message.created_at).limit(limit)
    )).scalars().all()
    return [{"id": str(m.id), "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in rows]
