"""M4 Memory Consolidation — dedup, merge, contradiction resolution.

Runs periodically (or after extraction) to keep memory clean and coherent.
LLM decides per-fact: INSERT / UPDATE / DELETE / SKIP.
"""
import json
import logging
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from db.models import Memory
from llm.gateway import get_llm
from llm.embeddings import embed_text

logger = logging.getLogger(__name__)

CONSOLIDATE_PROMPT = """Bạn là memory manager. So sánh fact MỚI với các memories HIỆN CÓ.

Memories hiện có:
{existing}

Fact mới: "{new_fact}"

Trả về JSON (KHÔNG markdown):
{{"action": "INSERT|UPDATE|DELETE|SKIP", "target_id": "uuid nếu UPDATE/DELETE, rỗng nếu INSERT/SKIP", "merged_content": "nội dung merged nếu UPDATE, rỗng nếu khác", "reason": "1 câu giải thích"}}

Rules:
- INSERT: fact mới, chưa có tương tự
- UPDATE target_id: fact mới bổ sung/cập nhật fact cũ → merge
- DELETE target_id: fact mới mâu thuẫn fact cũ → xóa cũ rồi INSERT mới
- SKIP: fact đã tồn tại, không cần thêm"""

# Number of similar candidates to retrieve for comparison
CANDIDATE_TOP_K = 5


async def consolidate_fact(user_id: str, new_fact: str, db: AsyncSession) -> str:
    """Consolidate a single new fact against existing memories. Returns action taken."""
    if not settings.MEMORY_CONSOLIDATION_ENABLED:
        return "SKIP"

    uid = UUID(user_id)
    embedding = await embed_text(new_fact)

    # Find similar existing memories
    candidates = (await db.execute(
        select(Memory)
        .where(Memory.user_id == uid)
        .order_by(Memory.embedding.cosine_distance(embedding))
        .limit(CANDIDATE_TOP_K)
    )).scalars().all()

    if not candidates:
        # No existing memories — just insert
        db.add(Memory(user_id=uid, memory_type="semantic", content=new_fact, embedding=embedding, importance=0.6))
        await db.commit()
        return "INSERT"

    existing_str = "\n".join(f"- [{m.id}] {m.content}" for m in candidates)

    try:
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(CONSOLIDATE_PROMPT.format(existing=existing_str, new_fact=new_fact))
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        logger.exception("Consolidation LLM failed, falling back to INSERT")
        db.add(Memory(user_id=uid, memory_type="semantic", content=new_fact, embedding=embedding, importance=0.6))
        await db.commit()
        return "INSERT"

    action = data.get("action", "SKIP").upper()
    target_id = data.get("target_id", "")

    try:
        target_uuid = UUID(target_id) if target_id else None
    except (ValueError, AttributeError):
        target_uuid = None

    if action == "INSERT":
        db.add(Memory(user_id=uid, memory_type="semantic", content=new_fact, embedding=embedding, importance=0.6))
    elif action == "UPDATE" and target_uuid:
        merged = data.get("merged_content", new_fact)
        merged_emb = await embed_text(merged)
        target = await db.get(Memory, target_uuid)
        if target and target.user_id == uid:
            target.content = merged
            target.embedding = merged_emb
    elif action == "DELETE" and target_uuid:
        await db.execute(delete(Memory).where(Memory.id == target_uuid, Memory.user_id == uid))
        db.add(Memory(user_id=uid, memory_type="semantic", content=new_fact, embedding=embedding, importance=0.6))
    # SKIP: do nothing

    await db.commit()
    logger.info(f"Consolidation: {action} for user={user_id}")
    return action
