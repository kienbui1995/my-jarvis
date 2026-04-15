"""Community edition agent nodes — basic fallbacks when Pro intelligence modules are not available.

These provide a working (but simpler) agent pipeline:
- Router: keyword-based classification, no LLM routing
- Agent loop: direct LLM call with tools
- No skills matching, no memory consolidation, no proactive patterns
"""
from langchain_core.messages import AIMessage, SystemMessage

from agent.state import AgentState
from llm.gateway import get_llm


async def router_node(state: AgentState) -> dict:
    return {
        "intent": "general_chat",
        "complexity": "simple",
        "selected_model": "gemini-2.0-flash",
        "budget_remaining": 0.10,
        "hot_memory": "",
        "cold_memory": "",
        "injection_score": 0.0,
        "needs_planning": False,
    }


async def agent_loop_node(state: AgentState) -> dict:
    model = state.get("selected_model", "gemini-2.0-flash")
    llm = get_llm(model).bind_tools(state.get("mcp_tools", []))
    resp = await llm.ainvoke(state["messages"])
    return {"messages": [resp]}


async def response_node(state: AgentState) -> dict:
    final = state.get("final_response", "")
    if not final and state["messages"]:
        last = state["messages"][-1]
        final = last.content if isinstance(last, AIMessage) else ""
    return {"final_response": final}


async def post_process_node(state: AgentState) -> dict:
    return {}


async def evaluate_node(state: AgentState) -> dict:
    return {}


async def delegate_node(state: AgentState) -> dict:
    return {"delegation_result": "Delegation not available in Community edition."}


async def planner_node(state: AgentState) -> dict:
    last_msg = state["messages"][-1].content if state["messages"] else ""
    return {"execution_plan": {"steps": [last_msg], "request": last_msg, "goal": last_msg}, "current_step": 0, "step_results": []}


async def executor_node(state: AgentState) -> dict:
    model = state.get("selected_model", "gemini-2.0-flash")
    plan = state.get("execution_plan", {})
    step = plan.get("steps", [""])[state.get("current_step", 0)] if plan.get("steps") else ""
    llm = get_llm(model)
    resp = await llm.ainvoke(f"Thực hiện: {step}")
    return {"step_results": state.get("step_results", []) + [resp.content], "current_step": state.get("current_step", 0) + 1}


async def replan_node(state: AgentState) -> dict:
    return {"replan_count": state.get("replan_count", 0) + 1}


async def synthesize_node(state: AgentState) -> dict:
    results = state.get("step_results", [])
    return {"final_response": "\n".join(results)}


def route_after_planner(state: AgentState) -> str:
    if not state.get("execution_plan", {}).get("steps"):
        return "respond"
    return "executor"


def route_after_executor(state: AgentState) -> str:
    plan = state.get("execution_plan", {})
    steps = plan.get("steps", [])
    if state.get("current_step", 0) >= len(steps):
        return "synthesize"
    return "executor"


def route_after_replan(state: AgentState) -> str:
    return "respond"
