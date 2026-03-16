"""Memory tools — hybrid search (vector + keyword) with re-ranking."""
from typing import Annotated
from uuid import UUID

from langchain_core.tools import InjectedToolArg, tool
from sqlalchemy import or_, select

from db.models import Memory
from db.session import async_session
from llm.embeddings import embed_text


@tool
async def memory_save(
    content: str, memory_type: str = "semantic",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Lưu thông tin vào bộ nhớ. Args: content, memory_type (episodic/semantic/procedural)."""
    embedding = await embed_text(content)
    async with async_session() as db:
        m = Memory(
            user_id=UUID(user_id), memory_type=memory_type,
            content=content, embedding=embedding, importance=0.7,
        )
        db.add(m)
        await db.commit()
        return f"🧠 Đã ghi nhớ: {content[:80]}"


@tool
async def memory_search(
    query: str, limit: int = 5,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Tìm kiếm trong bộ nhớ bằng hybrid search (keyword + semantic). Args: query, limit."""
    uid = UUID(user_id)
    async with async_session() as db:
        # Vector search
        query_embedding = await embed_text(query)
        vector_q = (
            select(
                Memory.id, Memory.content, Memory.memory_type,
                Memory.embedding.cosine_distance(query_embedding).label("vdist"),
            )
            .where(Memory.user_id == uid, Memory.embedding.isnot(None))
            .order_by("vdist")
            .limit(limit * 2)
        )
        vector_results = (await db.execute(vector_q)).all()

        # Keyword search (ILIKE for Vietnamese)
        keywords = [w for w in query.split() if len(w) >= 2]
        keyword_results = []
        if keywords:
            conditions = [Memory.content.ilike(f"%{kw}%") for kw in keywords[:5]]
            kw_q = (
                select(Memory.id, Memory.content, Memory.memory_type)
                .where(Memory.user_id == uid, or_(*conditions))
                .limit(limit * 2)
            )
            keyword_results = (await db.execute(kw_q)).all()

        # RRF fusion (Reciprocal Rank Fusion)
        scores: dict[str, float] = {}
        content_map: dict[str, tuple[str, str]] = {}
        k = 60  # RRF constant

        for rank, row in enumerate(vector_results):
            mid = str(row.id)
            scores[mid] = scores.get(mid, 0) + 1 / (k + rank + 1)
            content_map[mid] = (row.content, row.memory_type)

        for rank, row in enumerate(keyword_results):
            mid = str(row.id)
            scores[mid] = scores.get(mid, 0) + 1 / (k + rank + 1)
            content_map[mid] = (row.content, row.memory_type)

        # Sort by fused score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        if not ranked:
            return "🧠 Không tìm thấy gì trong bộ nhớ."

        return "\n".join(
            f"- [{content_map[mid][1]}] {content_map[mid][0]}"
            for mid, _ in ranked
        )
