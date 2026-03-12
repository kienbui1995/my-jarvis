"""Response builder node — format final response for channel delivery."""
from agent.state import AgentState

# Quick reply suggestions based on detected intent
ZALO_SUGGESTIONS = {
    "task": ["Xem tasks", "Tạo task mới", "Tasks hôm nay"],
    "calendar": ["Xem lịch hôm nay", "Tạo sự kiện", "Lịch tuần này"],
    "finance": ["Chi tiêu hôm nay", "Tổng chi tháng này", "Thêm chi tiêu"],
    "default": ["Tạo task", "Xem lịch", "Chi tiêu hôm nay"],
}


def _detect_topic(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ("task", "việc", "công việc", "todo")):
        return "task"
    if any(w in t for w in ("lịch", "calendar", "meeting", "họp", "sự kiện")):
        return "calendar"
    if any(w in t for w in ("chi tiêu", "tiền", "expense", "thanh toán")):
        return "finance"
    return "default"


async def response_node(state: AgentState) -> dict:
    """Extract final text response — prefer delegation_result if available."""
    delegation = state.get("delegation_result", "")
    text = delegation if delegation else (state["messages"][-1].content if state["messages"] else "")

    result = {"final_response": text}

    # Add quick reply hints for Zalo channel
    if state.get("channel") == "zalo" and text:
        topic = _detect_topic(text)
        result["zalo_quick_replies"] = ZALO_SUGGESTIONS.get(topic, ZALO_SUGGESTIONS["default"])

    return result
