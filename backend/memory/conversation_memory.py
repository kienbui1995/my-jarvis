"""M2 Conversation Memory — SummaryBuffer pattern.

Keep last N turns verbatim, summarize older turns into rolling_summary.
"""
import logging
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models import Conversation, Message
from llm.gateway import get_llm
import core.redis as redis_pool

logger = logging.getLogger(__name__)

VERBATIM_TURNS = 10  # keep last N messages verbatim

SUMMARIZE_PROMPT = """Tóm tắt ngắn gọn đoạn hội thoại sau thành 2-4 câu, giữ lại thông tin quan trọng.
Nếu đã có tóm tắt trước đó, hãy merge vào.

Tóm tắt trước đó:
{previous_summary}

Đoạn hội thoại cần tóm tắt:
{conversation}"""


async def summarize_if_needed(conversation_id: UUID, db: AsyncSession) -> None:
    """Check turn count; if > VERBATIM_TURNS, summarize oldest turns."""
    if not settings.CONVO_MEMORY_ENABLED:
        return

    # Redis lock to prevent concurrent summarization
    r = redis_pool.get()
    lock_key = f"summarize_lock:{conversation_id}"
    acquired = await r.set(lock_key, "1", nx=True, ex=30)
    if not acquired:
        return

    try:
        count = (await db.execute(
            select(func.count()).where(Message.conversation_id == conversation_id)
        )).scalar() or 0

        if count <= VERBATIM_TURNS:
            return

        conv = await db.get(Conversation, conversation_id)
        if not conv:
            return

        # Get messages to summarize (oldest beyond verbatim window)
        overflow = count - VERBATIM_TURNS
        old_msgs = (await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(overflow)
        )).scalars().all()

        if not old_msgs:
            return

        convo_text = "\n".join(f"{m.role}: {m.content}" for m in old_msgs)
        prev_summary = conv.rolling_summary or ""

        try:
            llm = get_llm("gemini-2.0-flash")
            resp = await llm.ainvoke(SUMMARIZE_PROMPT.format(
                previous_summary=prev_summary or "(không có)",
                conversation=convo_text,
            ))
            new_summary = resp.content.strip()
        except Exception:
            logger.exception("Summarization failed")
            return

        # Update conversation + delete summarized messages
        conv.rolling_summary = new_summary
        conv.summary_turn_count = (conv.summary_turn_count or 0) + len(old_msgs)
        conv.total_turns = count
        await db.flush()

        msg_ids = [m.id for m in old_msgs]
        await db.execute(delete(Message).where(Message.id.in_(msg_ids)))
        await db.commit()

        logger.info(f"Summarized {len(old_msgs)} turns for conv {conversation_id}")
    finally:
        await r.delete(lock_key)


async def build_memory_context(conversation_id: UUID, db: AsyncSession) -> str:
    """Build context string: rolling_summary + recent messages (for system prompt injection)."""
    conv = await db.get(Conversation, conversation_id)
    if not conv or not conv.rolling_summary:
        return ""
    return f"[Tóm tắt hội thoại trước]: {conv.rolling_summary}"
