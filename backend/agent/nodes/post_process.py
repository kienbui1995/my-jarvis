"""Post-process node — memory extraction + usage logging (fire-and-forget background tasks)."""
import asyncio
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


async def _background_extract(messages: list, user_id: str) -> None:
    """Fire-and-forget: extract memories, KG, and preferences in background."""
    try:
        await extract_memories(messages, user_id=user_id)
    except Exception:
        logger.debug("Background memory extraction failed", exc_info=True)
    try:
        await extract_kg(messages, user_id)
    except Exception:
        logger.debug("Background KG extraction failed", exc_info=True)
    try:
        from memory.preference_learning import extract_preferences
        async with async_session() as db:
            await extract_preferences(messages, user_id, db)
    except Exception:
        logger.debug("Background preference extraction failed", exc_info=True)


async def post_process_node(state: AgentState) -> dict:
    user_id = state.get("user_id", "")
    model = state.get("selected_model", "")

    # 1. Log usage + record spend (fast, always awaited)
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

    # 2. Extract memories + KG + preferences (fire-and-forget, 3 LLM calls in background)
    if user_id and len(state["messages"]) >= 2:
        asyncio.create_task(_background_extract(list(state["messages"]), user_id))

    # 3. M47: Extract skill from plan-and-execute tasks (fire-and-forget)
    step_results = state.get("step_results", [])
    if user_id and len(step_results) >= 3:
        asyncio.create_task(_background_skill_extract(state))

    return {}


async def _background_skill_extract(state: dict) -> None:
    """Fire-and-forget: extract reusable skill from completed plan-and-execute task."""
    try:
        from memory.skill_learning import extract_skill_from_task, record_skill_execution
        import time

        user_id = state.get("user_id", "")
        plan = state.get("execution_plan", {})
        steps = state.get("step_results", [])
        final = state.get("final_response", "")
        matched = state.get("matched_skill", {})
        start_time = state.get("skill_execution_start", 0)

        async with async_session() as db:
            # If this was a skill execution, record it
            if matched.get("skill_id"):
                duration = time.time() - start_time if start_time else None
                await record_skill_execution(
                    matched["skill_id"], user_id,
                    input_summary=plan.get("goal", ""),
                    output_summary=final[:500],
                    steps=steps, success=True, duration=duration, db=db,
                )
            else:
                # Try to extract a new skill from this task
                task_desc = plan.get("goal", "") or (state["messages"][0].content if state["messages"] else "")
                await extract_skill_from_task(user_id, task_desc, steps, final, db)
    except Exception:
        logger.debug("Background skill extraction failed", exc_info=True)
