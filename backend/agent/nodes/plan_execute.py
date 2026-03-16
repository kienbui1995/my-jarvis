"""M3 Plan-and-Execute + M8 Human-in-the-Loop.

Sequential plan → execute → replan loop.
HITL: interrupt() for plans ≥3 steps or destructive actions.
"""
import json
import logging

from langchain_core.messages import AIMessage, SystemMessage
from langgraph.types import interrupt

from agent.state import AgentState
from agent.tools import all_tools
from core.config import settings
from core.context_guard import guard_context
from llm.gateway import get_llm

logger = logging.getLogger(__name__)

MAX_STEPS = 7
MAX_REPLANS = 2
HITL_STEP_THRESHOLD = 3
DESTRUCTIVE_TOOLS = {"task_update", "expense_log", "calendar_create"}

WORKFLOW_TEMPLATES = {
    "research": {
        "pattern": ["web_search", "summarize_url", "memory_save"],
        "hint": "Tìm → đọc chi tiết → lưu kết quả",
    },
    "trip_planning": {
        "pattern": ["web_search", "weather_vn", "calendar_create", "task_create"],
        "hint": "Tìm info → check thời tiết → tạo lịch → tạo todo list",
    },
    "weekly_review": {
        "pattern": ["task_list", "google_calendar_list", "budget_check", "memory_search"],
        "hint": "Xem tasks → xem lịch → check chi tiêu → review insights",
    },
    "email_digest": {
        "pattern": ["gmail_read", "news_vn", "memory_save"],
        "hint": "Đọc email → đọc tin tức → lưu tóm tắt",
    },
}

PLAN_PROMPT = """Bạn là planner cho AI assistant. Tạo kế hoạch thực hiện yêu cầu của user.

Tools có sẵn: {tool_names}

Workflow templates (dùng làm gợi ý nếu phù hợp):
{workflow_hints}

Trả về JSON (KHÔNG markdown):
{{"steps": ["bước 1", "bước 2", ...], "reasoning": "giải thích ngắn"}}

Rules:
- Tối đa {max_steps} bước
- Mỗi bước phải rõ ràng, actionable, nêu rõ tool cần dùng
- Nếu yêu cầu đơn giản, chỉ cần 1-2 bước
- Ưu tiên workflow template nếu khớp với yêu cầu"""

EXECUTE_PROMPT = """Thực hiện bước sau trong kế hoạch. Dùng tools nếu cần.

Kế hoạch tổng thể: {plan}
Kết quả các bước trước: {previous_results}

Bước hiện tại ({step_num}/{total}): {step}"""

REPLAN_PROMPT = """Đánh giá kết quả và quyết định tiếp theo.

Kế hoạch ban đầu: {plan}
Kết quả đã có: {results}

Trả về JSON (KHÔNG markdown):
{{"action": "continue|replan|done", "new_steps": ["bước mới nếu replan"], "summary": "tóm tắt"}}"""

SYNTHESIZE_PROMPT = """Tổng hợp kết quả thành câu trả lời cho user.

Yêu cầu gốc: {request}
Kế hoạch: {plan}
Kết quả: {results}

Trả lời ngắn gọn, thân thiện bằng tiếng Việt."""


async def planner_node(state: AgentState) -> dict:
    """Generate execution plan from user request."""
    last_msg = state["messages"][-1].content if state["messages"] else ""
    model = state.get("selected_model", "gemini-2.0-flash")
    tool_names = ", ".join(t.name for t in all_tools)

    workflow_hints = "\n".join(
        f"- {name}: {wf['hint']} (tools: {', '.join(wf['pattern'])})"
        for name, wf in WORKFLOW_TEMPLATES.items()
    )

    llm = get_llm(model)
    resp = await llm.ainvoke(PLAN_PROMPT.format(
        tool_names=tool_names, max_steps=MAX_STEPS,
        workflow_hints=workflow_hints,
    ) + f"\n\nYêu cầu: {last_msg}")

    try:
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
        steps = data.get("steps", [])[:MAX_STEPS]
    except Exception:
        logger.warning("Plan parsing failed, single-step fallback")
        steps = [last_msg]

    plan = {"steps": steps, "request": last_msg}

    # M8: HITL — interrupt if plan is complex or has destructive actions
    if settings.HITL_ENABLED and len(steps) >= HITL_STEP_THRESHOLD:
        approval = interrupt({
            "type": "plan_approval",
            "plan": steps,
            "message": f"Kế hoạch có {len(steps)} bước. Bạn có muốn tiếp tục?",
        })
        if approval and isinstance(approval, dict) and not approval.get("approved", True):
            return {
                "execution_plan": {},
                "needs_planning": False,
                "messages": [AIMessage(content="Đã hủy kế hoạch theo yêu cầu.")],
            }

    return {
        "execution_plan": plan,
        "current_step": 0,
        "step_results": [],
        "replan_count": 0,
    }


def route_after_planner(state: AgentState) -> str:
    """After planner: if plan was rejected or empty, skip to respond."""
    if not state.get("execution_plan") or not state["execution_plan"].get("steps"):
        return "respond"
    return "executor"


async def executor_node(state: AgentState) -> dict:
    """Execute current step using LLM + tools."""
    plan = state.get("execution_plan", {})
    steps = plan.get("steps", [])
    idx = state.get("current_step", 0)

    if idx >= len(steps):
        return {}

    step = steps[idx]
    model = state.get("selected_model", "gemini-2.0-flash")
    llm = get_llm(model).bind_tools(all_tools)

    prev_results = state.get("step_results", [])
    prompt = EXECUTE_PROMPT.format(
        plan=json.dumps(steps, ensure_ascii=False),
        previous_results=json.dumps(prev_results, ensure_ascii=False),
        step_num=idx + 1, total=len(steps), step=step,
    )

    messages = [SystemMessage(content=prompt)] + state["messages"]
    messages = guard_context(messages, model)

    resp = await llm.ainvoke(messages)

    # M8: HITL — interrupt if LLM wants to call destructive tools
    if settings.HITL_ENABLED and hasattr(resp, "tool_calls") and resp.tool_calls:
        destructive_calls = [tc["name"] for tc in resp.tool_calls if tc["name"] in DESTRUCTIVE_TOOLS]
        if destructive_calls:
            approval = interrupt({
                "type": "step_approval",
                "step": step,
                "step_num": idx + 1,
                "tools": destructive_calls,
                "message": f"Bước {idx + 1} sẽ dùng {', '.join(destructive_calls)}. Cho phép?",
            })
            if approval and isinstance(approval, dict) and not approval.get("approved", True):
                return {
                    "step_results": prev_results + [f"Bước {idx + 1}: Bị từ chối bởi user"],
                    "current_step": idx + 1,
                }

    result_text = resp.content or f"Step {idx + 1} completed"

    return {
        "messages": [resp],
        "step_results": prev_results + [f"Bước {idx + 1}: {result_text[:500]}"],
        "current_step": idx + 1,
    }


async def replan_node(state: AgentState) -> dict:
    """Evaluate progress and decide: continue / replan / done."""
    plan = state.get("execution_plan", {})
    steps = plan.get("steps", [])
    idx = state.get("current_step", 0)
    results = state.get("step_results", [])
    replan_count = state.get("replan_count", 0)

    # All steps done → synthesize
    if idx >= len(steps):
        return {"needs_planning": False}

    # Max replans reached → synthesize with what we have
    if replan_count >= MAX_REPLANS:
        return {"needs_planning": False}

    model = state.get("selected_model", "gemini-2.0-flash")
    llm = get_llm(model)

    resp = await llm.ainvoke(REPLAN_PROMPT.format(
        plan=json.dumps(steps, ensure_ascii=False),
        results=json.dumps(results, ensure_ascii=False),
    ))

    try:
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        return {"needs_planning": False}

    action = data.get("action", "done")

    if action == "replan" and data.get("new_steps"):
        new_steps = data["new_steps"][:MAX_STEPS]
        return {
            "execution_plan": {**plan, "steps": new_steps},
            "current_step": 0,
            "replan_count": replan_count + 1,
        }
    elif action == "continue":
        return {}  # continue to next executor step
    else:
        return {"needs_planning": False}


async def synthesize_node(state: AgentState) -> dict:
    """Combine all step results into final response."""
    plan = state.get("execution_plan", {})
    results = state.get("step_results", [])
    request = plan.get("request", "")
    model = state.get("selected_model", "gemini-2.0-flash")

    llm = get_llm(model)
    resp = await llm.ainvoke(SYNTHESIZE_PROMPT.format(
        request=request,
        plan=json.dumps(plan.get("steps", []), ensure_ascii=False),
        results=json.dumps(results, ensure_ascii=False),
    ))

    return {
        "messages": [AIMessage(content=resp.content)],
        "needs_planning": False,
        "execution_plan": {},
    }


# ── Routing functions ─────────────────────────────────────────

def route_after_executor(state: AgentState) -> str:
    """After executor: handle tool calls or go to replan."""
    last = state["messages"][-1] if state["messages"] else None
    if last and hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "replan"


def route_after_replan(state: AgentState) -> str:
    """After replan: continue executing or synthesize."""
    if state.get("needs_planning", True):
        return "executor"
    return "synthesize"
