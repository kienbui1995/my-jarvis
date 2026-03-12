"""Conversation service — manage conversation sessions."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Conversation, Message


async def get_or_create_conversation(db: AsyncSession, user_id: UUID, channel: str) -> Conversation:
    """Get active conversation or create new one."""
    # For MVP: one active conversation per user per channel
    from sqlalchemy import select
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id, Conversation.channel == channel, Conversation.ended_at.is_(None))
        .order_by(Conversation.started_at.desc())
        .limit(1)
    )
    conv = result.scalar_one_or_none()
    if conv:
        return conv

    conv = Conversation(user_id=user_id, channel=channel)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def save_message(db: AsyncSession, conversation_id: UUID, role: str, content: str, **kwargs) -> Message:
    msg = Message(conversation_id=conversation_id, role=role, content=content, **kwargs)
    db.add(msg)
    await db.commit()
    return msg


async def load_history(db: AsyncSession, conversation_id: UUID, limit: int = 20) -> list:
    """Load recent messages as LangChain message objects (excluding the latest user msg being processed)."""
    from langchain_core.messages import HumanMessage, AIMessage
    from sqlalchemy import select as sel
    result = await db.execute(
        sel(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit + 1)  # +1 because we just saved current msg
    )
    rows = list(result.scalars())
    # Skip the first row (the message we just saved), reverse to chronological
    rows = list(reversed(rows[1:]))
    msgs = []
    for r in rows:
        if r.role == "user":
            msgs.append(HumanMessage(content=r.content))
        elif r.role == "assistant":
            msgs.append(AIMessage(content=r.content))
    return msgs
