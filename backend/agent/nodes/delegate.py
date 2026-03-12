"""Delegate node — spawn specialist sub-agent, run tool loop, return result."""
import logging
from langchain_core.messages import SystemMessage, HumanMessage

from agent.state import AgentState
from agent.registry import SPECIALISTS
from agent.tools import all_tools
from llm.gateway import get_llm

logger = logging.getLogger(__name__)

# Build name→tool lookup
_TOOL_MAP = {t.name: t for t in all_tools}

MAX_SPECIALIST_STEPS = 5


async def delegate_node(state: AgentState) -> dict:
    """Run specialist sub-agent with isolated context. Fallback to empty result on failure."""
    target = state.get("delegation_target", "")
    spec = SPECIALISTS.get(target)
    if not spec:
        logger.warning(f"Unknown specialist: {target}")
        return {"delegation_result": ""}

    try:
        # Resolve tools for this specialist
        tools = [_TOOL_MAP[n] for n in spec["tools"] if n in _TOOL_MAP]
        llm = get_llm(spec["model"]).bind_tools(tools) if tools else get_llm(spec["model"])

        # Isolated context: system prompt + user's last message only
        user_msg = state["messages"][-1].content if state["messages"] else ""
        messages = [
            SystemMessage(content=spec["system_prompt"]),
            HumanMessage(content=user_msg),
        ]

        # Tool loop (max steps to prevent runaway)
        for _ in range(MAX_SPECIALIST_STEPS):
            resp = await llm.ainvoke(messages)
            messages.append(resp)

            if not resp.tool_calls:
                # Final text response from specialist
                content = resp.content
                if isinstance(content, list):
                    content = "".join(c.get("text", str(c)) if isinstance(c, dict) else str(c) for c in content)
                return {"delegation_result": content, "delegation_count": state.get("delegation_count", 0) + 1}

            # Execute tool calls
            from langchain_core.messages import ToolMessage
            for tc in resp.tool_calls:
                tool = _TOOL_MAP.get(tc["name"])
                if tool:
                    try:
                        args = {**tc["args"], "user_id": state.get("user_id", "")}
                        result = await tool.ainvoke(args)
                    except Exception as e:
                        result = f"Error: {e}"
                else:
                    result = f"Unknown tool: {tc['name']}"
                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

        # Max steps reached — use last response
        return {"delegation_result": messages[-1].content if hasattr(messages[-1], "content") else ""}

    except Exception as e:
        logger.error(f"Specialist {target} failed: {e}")
        return {"delegation_result": ""}
