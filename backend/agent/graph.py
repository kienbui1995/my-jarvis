"""LangGraph agent pipeline — route → (delegate | agent_loop) → respond → evaluate → post_process."""
from langgraph.graph import END, StateGraph

from agent.state import AgentState
from agent.tools import all_tools
from core.config import settings

# Graceful import — Community edition uses basic fallbacks
try:
    from agent.nodes.router import router_node
    from agent.nodes.agent_loop import agent_loop_node
    from agent.nodes.response import response_node
    from agent.nodes.post_process import post_process_node
    from agent.nodes.evaluate import evaluate_node
    from agent.nodes.delegate import delegate_node
    from agent.nodes.plan_execute import (
        planner_node, executor_node, replan_node, synthesize_node,
        route_after_planner, route_after_executor, route_after_replan,
    )
except ImportError:
    from agent.nodes_community import (  # noqa: F401
        router_node, agent_loop_node, response_node, post_process_node,
        evaluate_node, delegate_node, planner_node, executor_node,
        replan_node, synthesize_node, route_after_planner,
        route_after_executor, route_after_replan,
    )

# Build tool lookup
_tools_by_name = {t.name: t for t in all_tools}


async def tools_node(state: AgentState) -> dict:
    """Execute tool calls with user_id injected from state."""
    import logging
    logger = logging.getLogger(__name__)
    from langchain_core.messages import ToolMessage
    from core.evidence import log_evidence
    from db.models.preference import UserToolPermission
    from sqlalchemy import select
    import time
    user_id = state.get("user_id", "")
    conv_id = state.get("conversation_id", "")
    last = state["messages"][-1]
    results = []

    # M11: Load user tool permissions (cached in Redis 60s)
    disabled_tools = set()
    if user_id and settings.TOOL_PERMISSIONS_ENABLED:
        try:
            import core.redis as _redis
            r = _redis.get()
            cache_key = f"tool_perms:{user_id}"
            cached = await r.get(cache_key)
            if cached:
                disabled_tools = set(cached.split(",")) if cached != "" else set()
            else:
                from uuid import UUID as _UUID
                from db.session import async_session as _session
                async with _session() as db:
                    perms = (await db.execute(
                        select(UserToolPermission).where(
                            UserToolPermission.user_id == _UUID(user_id),
                            UserToolPermission.enabled == False,
                        )
                    )).scalars().all()
                    disabled_tools = {p.tool_name for p in perms}
                await r.setex(cache_key, 60, ",".join(disabled_tools))
        except Exception:
            pass

    for tc in (last.tool_calls or []):
        # M11: Check permission
        if tc["name"] in disabled_tools:
            results.append(ToolMessage(content=f"Tool {tc['name']} bị vô hiệu hóa bởi user", tool_call_id=tc["id"]))
            continue

        tool = _tools_by_name.get(tc["name"])
        is_mcp = False
        if not tool:
            # Check MCP tools
            mcp_tools = state.get("mcp_tools", [])
            tool = next((t for t in mcp_tools if t.name == tc["name"]), None)
            is_mcp = tool is not None
        if not tool:
            results.append(ToolMessage(content=f"Tool {tc['name']} not found", tool_call_id=tc["id"]))
            continue
        args = {**tc["args"]} if is_mcp else {**tc["args"], "user_id": user_id}
        t0 = time.monotonic()
        try:
            output = await tool.ainvoke(args)
            ms = int((time.monotonic() - t0) * 1000)
            logger.info(f"Tool {tc['name']} OK: {str(output)[:100]}")
            await log_evidence(user_id, conv_id, "tools", "tool_call", tool_name=tc["name"], tool_input=tc["args"], tool_output=str(output)[:2000], duration_ms=ms)
        except Exception as e:
            ms = int((time.monotonic() - t0) * 1000)
            output = f"Error: {e}"
            logger.exception(f"Tool {tc['name']} failed")
            await log_evidence(user_id, conv_id, "tools", "tool_error", tool_name=tc["name"], tool_input=tc["args"], error=str(e), duration_ms=ms)
        results.append(ToolMessage(content=str(output), tool_call_id=tc["id"]))
    return {"messages": results, "tool_calls_count": state.get("tool_calls_count", 0) + 1}


MAX_TOOL_ROUNDS = 10


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1] if state["messages"] else None
    if last and hasattr(last, "tool_calls") and last.tool_calls:
        if state.get("tool_calls_count", 0) >= MAX_TOOL_ROUNDS:
            return "respond"
        return "tools"
    return "respond"


def should_retry(state: AgentState) -> str:
    if 0 < state.get("retry_count", 0) <= 1:
        return "agent_loop"
    return "post_process"


def route_after_router(state: AgentState) -> str:
    """After route: plan, delegate, or agent_loop."""
    if state.get("needs_planning") and settings.PLANNING_ENABLED:
        return "planner"
    if state.get("delegation_target"):
        return "delegate"
    return "agent_loop"


def route_after_tools(state: AgentState) -> str:
    """After tools: return to executor (if planning) or agent_loop."""
    if state.get("needs_planning") and state.get("execution_plan"):
        return "executor"
    return "agent_loop"


def route_after_delegate(state: AgentState) -> str:
    """After delegate: if specialist returned result → respond, else fallback to agent_loop."""
    if state.get("delegation_result"):
        return "respond"
    return "agent_loop"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("route", router_node)
    graph.add_node("agent_loop", agent_loop_node)
    graph.add_node("tools", tools_node)
    graph.add_node("delegate", delegate_node)
    graph.add_node("respond", response_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("post_process", post_process_node)
    # M3: Plan-and-Execute nodes
    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("replan", replan_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("route")
    graph.add_conditional_edges("route", route_after_router, {
        "delegate": "delegate", "agent_loop": "agent_loop", "planner": "planner",
    })
    graph.add_conditional_edges("delegate", route_after_delegate, {"respond": "respond", "agent_loop": "agent_loop"})
    graph.add_conditional_edges("agent_loop", should_continue, {"tools": "tools", "respond": "respond"})
    graph.add_conditional_edges("tools", route_after_tools, {"agent_loop": "agent_loop", "executor": "executor"})
    graph.add_edge("respond", "evaluate")
    graph.add_conditional_edges("evaluate", should_retry, {"agent_loop": "agent_loop", "post_process": "post_process"})
    graph.add_edge("post_process", END)

    # M3: Plan-Execute edges
    graph.add_conditional_edges("planner", route_after_planner, {"executor": "executor", "respond": "respond"})
    graph.add_conditional_edges("executor", route_after_executor, {"tools": "tools", "replan": "replan"})
    graph.add_conditional_edges("replan", route_after_replan, {"executor": "executor", "synthesize": "synthesize"})
    graph.add_edge("synthesize", "respond")

    return graph


_graph = build_graph()
# Compiled without checkpointer (sync init). Use get_jarvis_graph() for checkpointed version.
jarvis_graph = _graph.compile()

_checkpointed_graph = None


async def get_jarvis_graph():
    """Get graph compiled with PostgreSQL checkpointer (M7). Cached after first call."""
    global _checkpointed_graph
    if not settings.CHECKPOINTING_ENABLED:
        return jarvis_graph
    if _checkpointed_graph is not None:
        return _checkpointed_graph
    from core.checkpointer import get_checkpointer
    checkpointer = await get_checkpointer()
    _checkpointed_graph = _graph.compile(checkpointer=checkpointer)
    return _checkpointed_graph
