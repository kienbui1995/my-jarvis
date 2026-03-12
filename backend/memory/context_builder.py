"""Context builder — assemble full LLM context from hot + cold memory."""
from sqlalchemy.ext.asyncio import AsyncSession

from memory.service import load_hot_memory, search_cold_memory


async def build_context(user_id: str, query_embedding: list[float] | None, db: AsyncSession) -> dict[str, str]:
    """Build context dict for injection into agent system prompt.

    Returns: {"hot_memory": str, "cold_memory": str}
    """
    hot = await load_hot_memory(user_id, db)

    cold = ""
    if query_embedding:
        memories = await search_cold_memory(user_id, query_embedding, db, limit=3)
        if memories:
            cold = "\n".join(f"[{m['type']}] {m['content']}" for m in memories)

    return {"hot_memory": hot, "cold_memory": cold}
