"""Agent loop node — core LLM reasoning with tool calling."""
from langchain_core.messages import SystemMessage

from agent.state import AgentState
from agent.tools import all_tools
from core.context_guard import guard_context
from llm.cache import with_cache_control
from llm.gateway import get_llm

SYSTEM_PROMPT = """Bạn là MY JARVIS — trợ lý AI cá nhân thông minh, nói tiếng Việt tự nhiên.

{user_preferences}

Nguyên tắc:
- Trả lời ngắn gọn, thân thiện, đúng trọng tâm
- Dùng tool khi cần hành động — LUÔN ưu tiên tool thay vì trả lời chung chung
- Luôn nhớ context của user từ memory
- Nếu không chắc, hỏi lại thay vì đoán
- KHÔNG BAO GIỜ hỏi user_id — hệ thống tự inject
- Nếu tool lỗi, thử tool khác hoặc giải thích lỗi rõ ràng
- Tool có prefix "mcp_" là từ MCP server bên ngoài — dùng khi built-in tools không đủ

Hướng dẫn chọn tool:
- "thời tiết/nhiệt độ/trời mưa" → weather_vn
- "tin tức/báo/news" → news_vn
- "task/việc/công việc/deadline" → task_create/task_list/task_update
- "lịch/hẹn/cuộc họp/meeting" → calendar_create/calendar_list hoặc google_calendar_list
- "email/mail" → gmail_read/gmail_send
- "nhớ/lưu/ghi nhớ" → memory_save | "nhớ gì/biết gì về" → memory_search
- "ghi chú/note/memo" → note_save/note_search/note_list
- "chi tiêu/tiền/mua" → expense_log | "ngân sách/budget" → budget_check
- "tìm/search/tra cứu" → web_search | "tóm tắt URL/link" → summarize_url
- "mở trang/xem web/browse" → browse_web | "chụp trang" → browse_screenshot
- "ảnh/hình/file/hóa đơn" → analyze_file/ocr_file
- Câu hỏi đơn giản (chào, hỏi giờ, nói chuyện) → trả lời trực tiếp, KHÔNG dùng tool

{hot_memory}
{cold_memory}"""


async def agent_loop_node(state: AgentState) -> dict:
    """Call routed LLM with tools bound. Returns AIMessage (possibly with tool_calls)."""
    model = state.get("selected_model", "gemini-2.0-flash")

    tools = list(all_tools)
    mcp_tools = state.get("mcp_tools", [])
    if mcp_tools:
        tools.extend(mcp_tools)

    llm = get_llm(model).bind_tools(tools)

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
