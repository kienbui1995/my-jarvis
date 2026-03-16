"""Multi-agent collaboration — parallel sub-agents for complex tasks."""
import asyncio
import json
import logging

from langchain_core.messages import AIMessage, HumanMessage

from agent.state import AgentState
from agent.tools import all_tools
from llm.gateway import get_llm

logger = logging.getLogger(__name__)

DECOMPOSE_PROMPT = """Phân tích yêu cầu và chia thành sub-tasks ĐỘC LẬP có thể chạy song song.

Trả về JSON (KHÔNG markdown):
{{"subtasks": ["subtask 1", "subtask 2", ...], "aggregation": "cách tổng hợp kết quả"}}

Rules:
- Chỉ chia nếu có >= 2 parts thực sự độc lập
- Nếu không thể chia, trả về {{"subtasks": [], "aggregation": ""}}
- Tối đa 4 subtasks

Yêu cầu: {request}"""

AGGREGATE_PROMPT = """Tổng hợp kết quả từ nhiều sub-agents thành câu trả lời hoàn chỉnh.

Yêu cầu gốc: {request}
Hướng dẫn tổng hợp: {aggregation}

Kết quả:
{results}

Trả lời ngắn gọn, mạch lạc bằng tiếng Việt."""


async def _run_sub_agent(prompt: str, user_id: str, model: str) -> str:
    """Run a single sub-agent with its own tool access."""
    try:
        llm = get_llm(model).bind_tools(all_tools)
        resp = await llm.ainvoke([HumanMessage(content=prompt)])
        return resp.content if isinstance(resp.content, str) else str(resp.content)
    except Exception as e:
        return f"[Lỗi: {e}]"


async def multi_agent_node(state: AgentState) -> dict:
    """Decompose request into parallel sub-tasks, execute, aggregate."""
    last_msg = state["messages"][-1].content if state["messages"] else ""
    model = state.get("selected_model", "gemini-2.0-flash")
    user_id = state.get("user_id", "")

    # Step 1: Decompose
    llm = get_llm(model)
    resp = await llm.ainvoke(DECOMPOSE_PROMPT.format(request=last_msg))
    try:
        data = json.loads(
            resp.content.strip().removeprefix("```json").removesuffix("```").strip()
        )
        subtasks = data.get("subtasks", [])[:4]
        aggregation = data.get("aggregation", "")
    except Exception:
        subtasks = []
        aggregation = ""

    # If can't decompose, return empty (will fall through to normal agent_loop)
    if not subtasks:
        return {}

    logger.info(f"Multi-agent: {len(subtasks)} subtasks for user={user_id}")

    # Step 2: Execute sub-agents in parallel
    results = await asyncio.gather(
        *[_run_sub_agent(st, user_id, model) for st in subtasks]
    )

    # Step 3: Aggregate
    results_text = "\n\n".join(
        f"**Sub-task {i+1}** ({subtasks[i][:50]}): {r}"
        for i, r in enumerate(results)
    )
    agg_resp = await llm.ainvoke(AGGREGATE_PROMPT.format(
        request=last_msg, aggregation=aggregation, results=results_text,
    ))

    return {
        "messages": [AIMessage(content=agg_resp.content)],
        "final_response": agg_resp.content,
    }
