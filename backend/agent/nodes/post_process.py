"""Post-process node — memory extraction + usage logging (async, non-blocking)."""
import logging
from uuid import UUID

from langchain_core.messages import AIMessage

from agent.state import AgentState
from db.models import LLMUsage
from db.session import async_session
from llm.budget import record_spend
from memory.extraction import extract_memories
from memory.knowledge_graph import extract_and_store as extract_kg

logger = logging.getLogger(__name__)


def _estimate_cost(model: str, messages: list) -> tuple[int, int, float]:
    """Rough token/cost estimation from messages."""
    # Approximate: 1 token ≈ 4 chars
    input_chars = sum(len(m.content) for m in messages if not isinstance(m, AIMessage))
    output_chars = sum(len(m.content) for m in messages if isinstance(m, AIMessage))
    input_tokens = input_chars // 4
    output_tokens = output_chars // 4

    costs_per_m = {"gemini-2.0-flash": 0.10, "claude-haiku-4.5": 1.0, "claude-sonnet-4.6": 3.0}
    rate = costs_per_m.get(model, 0.5)
    cost = (input_tokens + output_tokens) * rate / 1_000_000
    return input_tokens, output_tokens, cost


async def post_process_node(state: AgentState) -> dict:
    user_id = state.get("user_id", "")
    model = state.get("selected_model", "")

    # 1. Log usage + record spend
    try:
        input_t, output_t, cost = _estimate_cost(model, state["messages"])
        if user_id and cost > 0:
            await record_spend(user_id, cost)
            async with async_session() as db:
                db.add(LLMUsage(
                    user_id=UUID(user_id), model=model,
                    input_tokens=input_t, output_tokens=output_t,
                    cost=cost, task_type=state.get("intent", ""),
                ))
                await db.commit()
    except Exception:
        logger.exception("Failed to log usage")

    # 2. Extract memories (async, best-effort)
    try:
        if user_id and len(state["messages"]) >= 2:
            await extract_memories(state["messages"], user_id=user_id)
            await extract_kg(state["messages"], user_id)
    except Exception:
        logger.exception("Failed to extract memories")

    # 3. M5: Extract user preferences
    try:
        if user_id and len(state["messages"]) >= 2:
            from memory.preference_learning import extract_preferences
            async with async_session() as db:
                await extract_preferences(state["messages"], user_id, db)
    except Exception:
        logger.exception("Failed to extract preferences")

    return {}
