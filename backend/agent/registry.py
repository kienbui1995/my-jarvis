"""Specialist agent registry — model, tools, system prompt per domain."""

SPECIALISTS = {
    "task": {
        "model": "gemini-2.0-flash",
        "tools": ["task_create", "task_list", "task_update"],
        "system_prompt": (
            "Bạn là chuyên gia quản lý công việc. Giúp user tạo, cập nhật, "
            "theo dõi task. Trả lời ngắn gọn bằng tiếng Việt."
        ),
    },
    "calendar": {
        "model": "gemini-2.0-flash",
        "tools": ["calendar_create", "calendar_list"],
        "system_prompt": (
            "Bạn là chuyên gia lịch trình. Giúp user tạo sự kiện, kiểm tra "
            "lịch, phát hiện xung đột. Trả lời ngắn gọn bằng tiếng Việt."
        ),
    },
    "research": {
        "model": "gemini-2.0-flash",
        "tools": ["web_search", "summarize_url", "memory_search", "graph_search"],
        "system_prompt": (
            "Bạn là chuyên gia nghiên cứu. Tìm kiếm web, tóm tắt thông tin, "
            "phân tích chuyên sâu. Trả lời chi tiết bằng tiếng Việt."
        ),
    },
    "finance": {
        "model": "gemini-2.0-flash",
        "tools": ["expense_log", "budget_check"],
        "system_prompt": (
            "Bạn là chuyên gia tài chính cá nhân. Giúp user ghi chi tiêu, "
            "phân tích ngân sách. Trả lời ngắn gọn bằng tiếng Việt."
        ),
    },
    "memory": {
        "model": "gemini-2.0-flash",
        "tools": ["memory_search", "graph_search"],
        "system_prompt": (
            "Bạn là chuyên gia trí nhớ. Tìm kiếm ký ức, knowledge graph, "
            "trả lời câu hỏi dựa trên dữ liệu đã lưu. Tiếng Việt."
        ),
    },
}

# Keywords → specialist mapping for router
SPECIALIST_KEYWORDS = {
    "task": {"tạo task", "thêm việc", "todo", "công việc", "deadline", "hoàn thành task", "cập nhật task"},
    "calendar": {"lịch", "cuộc họp", "hẹn", "sự kiện", "meeting", "nhắc nhở", "schedule"},
    "research": {"nghiên cứu", "tìm hiểu", "phân tích", "tóm tắt", "so sánh", "research", "analyze"},
    "finance": {"chi tiêu", "ngân sách", "expense", "budget", "tiền", "thanh toán", "hóa đơn"},
    "memory": {"nhớ gì về", "tôi đã nói", "lịch sử", "trước đó", "nhắc lại"},
}
