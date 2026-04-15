"""M50 Document Generation — generate reports, emails, summaries from templates.

Supports markdown output. PDF export via markdown→HTML→PDF pipeline.
"""
import logging
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg

from llm.gateway import get_llm

logger = logging.getLogger(__name__)

TEMPLATES = {
    "report": {
        "name": "Báo cáo",
        "prompt": """Viết báo cáo chuyên nghiệp bằng tiếng Việt về chủ đề: {topic}

Dữ liệu/context: {context}

Format markdown:
# Tiêu đề báo cáo
## 1. Tổng quan
## 2. Phân tích chi tiết
## 3. Số liệu quan trọng
## 4. Kết luận & Đề xuất

Yêu cầu: ngắn gọn, chuyên nghiệp, có số liệu cụ thể nếu có.""",
    },
    "email": {
        "name": "Email",
        "prompt": """Viết email bằng tiếng Việt.

Người nhận: {recipient}
Chủ đề: {topic}
Context: {context}
Tone: {tone}

Format:
Chào [tên],

[Nội dung]

Trân trọng,
[Tên user]""",
    },
    "summary": {
        "name": "Tóm tắt",
        "prompt": """Tóm tắt nội dung sau bằng tiếng Việt, ngắn gọn và rõ ràng.

Nội dung gốc: {context}

Format:
## Tóm tắt
- Điểm chính 1
- Điểm chính 2
- ...

## Kết luận
[1-2 câu]""",
    },
    "meeting_notes": {
        "name": "Biên bản họp",
        "prompt": """Viết biên bản họp từ nội dung sau:

Cuộc họp: {topic}
Nội dung: {context}

Format markdown:
# Biên bản họp: {topic}
**Ngày:** [hôm nay]

## Tham dự
## Nội dung thảo luận
## Quyết định
## Action items
| # | Việc cần làm | Người phụ trách | Deadline |""",
    },
}


@tool
async def generate_document(
    doc_type: str,
    topic: str,
    context: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
    recipient: str = "",
    tone: str = "professional",
) -> str:
    """Tạo tài liệu (report, email, summary, meeting_notes). Args: doc_type, topic, context."""
    template = TEMPLATES.get(doc_type)
    if not template:
        available = ", ".join(TEMPLATES.keys())
        return f"Loại tài liệu không hợp lệ. Chọn: {available}"

    prompt = template["prompt"].format(
        topic=topic, context=context or "Không có context bổ sung",
        recipient=recipient, tone=tone,
    )

    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(prompt)
    return resp.content
