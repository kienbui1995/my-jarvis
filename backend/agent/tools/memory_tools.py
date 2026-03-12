"""Memory tools — wired to DB + pgvector + embeddings, user_id auto-injected."""
from typing import Annotated
from uuid import UUID

from langchain_core.tools import tool, InjectedToolArg
from sqlalchemy import select

from db.models import Memory
from db.session import async_session
from llm.embeddings import embed_text


@tool
async def memory_save(
    content: str, memory_type: str = "semantic",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Lưu thông tin quan trọng vào bộ nhớ. Args: content, memory_type (episodic/semantic/procedural)."""
    embedding = await embed_text(content)
    async with async_session() as db:
        m = Memory(user_id=UUID(user_id), memory_type=memory_type, content=content, embedding=embedding, importance=0.7)
        db.add(m)
        await db.commit()
        return f"🧠 Đã ghi nhớ: {content[:80]}"


@tool
async def memory_search(
    query: str, limit: int = 5,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Tìm kiếm trong bộ nhớ cá nhân bằng semantic search. Args: query, limit."""
    query_embedding = await embed_text(query)
    async with async_session() as db:
        result = await db.execute(
            select(Memory)
            .where(Memory.user_id == UUID(user_id), Memory.embedding.isnot(None))
            .order_by(Memory.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        memories = result.scalars().all()
        if not memories:
            return "🧠 Không tìm thấy gì trong bộ nhớ."
        return "\n".join(f"- [{m.memory_type}] {m.content}" for m in memories)
