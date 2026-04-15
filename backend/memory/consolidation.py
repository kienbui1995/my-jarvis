"""M4 Memory Consolidation — dedup, merge, contradiction resolution.

Runs periodically (or after extraction) to keep memory clean and coherent.
LLM decides per-fact: INSERT / UPDATE / DELETE / SKIP.
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

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

BATCH_COMPRESS_PROMPT = """Bạn là memory compressor. Nhóm các memories tương tự thành 1 fact ngắn gọn.

Memories:
{memories}

Trả về JSON array (KHÔNG markdown):
[{{"merged_content": "fact tổng hợp ngắn gọn", "source_ids": ["uuid1", "uuid2"], "importance": 0.0-1.0}}]

Rules:
- Gộp memories trùng lặp/tương tự thành 1
- Giữ nguyên memories quan trọng/unique
- importance: 0.8+ cho facts quan trọng (goals, preferences), 0.3- cho trivial"""

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

    await db.commit()
    logger.info(f"Consolidation: {action} for user={user_id}")
    return action


# ── M45: Batch consolidation (weekly cron) ───────────────────

async def batch_consolidate_user(user_id: UUID, db: AsyncSession) -> dict:
    """Compress old memories for a single user. Returns stats."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    old_memories = (await db.execute(
        select(Memory)
        .where(Memory.user_id == user_id, Memory.created_at < cutoff, Memory.memory_type == "semantic")
        .order_by(Memory.importance.desc())
        .limit(100)
    )).scalars().all()

    if len(old_memories) < 5:
        return {"user": str(user_id), "compressed": 0, "deleted": 0}

    memories_str = "\n".join(f"- [{m.id}] (imp={m.importance:.1f}) {m.content}" for m in old_memories)

    try:
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(BATCH_COMPRESS_PROMPT.format(memories=memories_str))
        groups = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        logger.exception(f"Batch consolidation failed for user={user_id}")
        return {"user": str(user_id), "compressed": 0, "deleted": 0, "error": True}

    compressed = 0
    deleted = 0
    for group in groups:
        source_ids = group.get("source_ids", [])
        if len(source_ids) < 2:
            continue
        merged = group.get("merged_content", "")
        imp = min(group.get("importance", 0.5), 1.0)
        if not merged:
            continue

        # Delete old, insert merged
        valid_ids = []
        for sid in source_ids:
            try:
                valid_ids.append(UUID(sid))
            except (ValueError, AttributeError):
                pass
        if valid_ids:
            await db.execute(delete(Memory).where(Memory.id.in_(valid_ids), Memory.user_id == user_id))
            deleted += len(valid_ids)

        emb = await embed_text(merged)
        db.add(Memory(user_id=user_id, memory_type="semantic", content=merged, embedding=emb, importance=imp))
        compressed += 1

    await db.commit()
    logger.info(f"Batch consolidation user={user_id}: compressed={compressed}, deleted={deleted}")
    return {"user": str(user_id), "compressed": compressed, "deleted": deleted}


async def run_batch_consolidation() -> list[dict]:
    """Run batch consolidation for all users. Called by ARQ cron."""
    from db.session import async_session

    async with async_session() as db:
        user_ids = (await db.execute(
            select(Memory.user_id).distinct()
        )).scalars().all()

    results = []
    for uid in user_ids:
        async with async_session() as db:
            try:
                r = await batch_consolidate_user(uid, db)
                results.append(r)
            except Exception:
                logger.exception(f"Consolidation failed for user={uid}")
    return results


# ── M46: Memory decay ────────────────────────────────────────

async def run_memory_decay() -> int:
    """Decay importance of stale memories + cleanup very low ones. Called by ARQ cron."""
    from db.session import async_session

    now = datetime.now(timezone.utc)
    async with async_session() as db:
        # Decay: reduce importance by 5% for memories not accessed in 14+ days
        stale_cutoff = now - timedelta(days=14)
        await db.execute(
            update(Memory)
            .where(
                Memory.importance > 0.1,
                sa.or_(
                    Memory.last_accessed < stale_cutoff,
                    sa.and_(Memory.last_accessed.is_(None), Memory.created_at < stale_cutoff),
                ),
            )
            .values(importance=Memory.importance * 0.95)
        )

        # Cleanup: delete memories with very low importance + old + never accessed
        cleanup_cutoff = now - timedelta(days=30)
        result = await db.execute(
            delete(Memory).where(
                Memory.importance < 0.15,
                Memory.created_at < cleanup_cutoff,
                Memory.access_count == 0,
            )
        )
        cleaned = result.rowcount

        await db.commit()
        logger.info(f"Memory decay: cleaned {cleaned} stale memories")
        return cleaned
