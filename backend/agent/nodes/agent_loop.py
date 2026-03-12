"""Agent loop node — core LLM reasoning with tool calling."""
from langchain_core.messages import SystemMessage

from agent.state import AgentState
from agent.tools import all_tools
from llm.gateway import get_llm
from llm.cache import with_cache_control
from core.context_guard import guard_context

SYSTEM_PROMPT = """Bạn là MY JARVIS — trợ lý AI cá nhân thông minh, nói tiếng Việt tự nhiên.

{user_preferences}

Nguyên tắc:
- Trả lời ngắn gọn, thân thiện, đúng trọng tâm
- Dùng tool khi cần hành động (tạo task, xem lịch, ghi nhớ, tìm kiếm)
- Luôn nhớ context của user từ memory
- Nếu không chắc, hỏi lại thay vì đoán
- KHÔNG BAO GIỜ hỏi user_id — hệ thống tự inject

{hot_memory}
{cold_memory}"""


async def agent_loop_node(state: AgentState) -> dict:
    """Call routed LLM with tools bound. Returns AIMessage (possibly with tool_calls)."""
    model = state.get("selected_model", "gemini-2.0-flash")
    llm = get_llm(model).bind_tools(all_tools)

    sys_prompt = SYSTEM_PROMPT.format(
        hot_memory=state.get("hot_memory", ""),
        cold_memory=state.get("cold_memory", ""),
        user_preferences=state.get("user_preferences", ""),
    )

    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    messages = with_cache_control(messages, model)

    # M6: Context Window Guard — trim if over budget
    messages = guard_context(messages, model)

    response = await llm.ainvoke(messages)
    return {"messages": [response]}
