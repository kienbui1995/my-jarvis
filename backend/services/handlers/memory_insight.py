"""Memory insight trigger — detect patterns from conversation history."""
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ProactiveTrigger
from db.models.conversation import Conversation
from llm.gateway import get_llm
from services.trigger_engine import TriggerHandler, register_handler

DEFAULT_MIN_CONVERSATIONS = 5

INSIGHT_PROMPT = """Phân tích các chủ đề hội thoại gần đây của user và tìm pattern/insight hữu ích.

Tóm tắt các cuộc hội thoại gần đây:
{summaries}

Nếu có pattern thú vị (ví dụ: user hỏi nhiều về 1 chủ đề, lặp lại cùng 1 vấn đề, có thói quen),
hãy đưa ra 1 gợi ý proactive ngắn gọn (tối đa 100 từ) bằng tiếng Việt.
Nếu không có gì đáng chú ý, trả về chính xác: SKIP"""


@register_handler
class MemoryInsightHandler(TriggerHandler):
    TRIGGER_TYPE = "memory_insight"
    LISTENS_TO = ["conversation.ended"]

    async def should_fire(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> bool:
        min_convos = (trigger.config or {}).get("min_conversations", DEFAULT_MIN_CONVERSATIONS)
        week_ago = datetime.utcnow() - timedelta(days=7)
        count = (await db.execute(
            select(func.count()).where(
                Conversation.user_id == trigger.user_id,
                Conversation.started_at >= week_ago,
            )
        )).scalar()
        return count >= min_convos

    async def build_message(self, event: dict, trigger: ProactiveTrigger, db: AsyncSession) -> str:
        week_ago = datetime.utcnow() - timedelta(days=7)
        convos = (await db.execute(
            select(Conversation).where(
                Conversation.user_id == trigger.user_id,
                Conversation.started_at >= week_ago,
            ).order_by(Conversation.started_at.desc()).limit(10)
        )).scalars().all()

        summaries = "\n".join(
            f"- {c.started_at.strftime('%d/%m')}: "
            f"{c.summary or c.rolling_summary or '(no summary)'}"
            for c in convos
        )
        if not summaries.strip():
            return ""

        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(INSIGHT_PROMPT.format(summaries=summaries))
        text = resp.content.strip()
        if text == "SKIP" or not text:
            return ""
        return f"💡 Insight: {text}"
