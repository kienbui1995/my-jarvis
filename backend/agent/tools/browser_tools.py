"""Browser automation tools — navigate, extract, click, fill, screenshot."""
from typing import Annotated

from langchain_core.tools import InjectedToolArg, tool

from services.browser import (
    click_and_extract,
    fill_and_submit,
    navigate_and_extract,
    screenshot_page,
)
from services.vision import analyze_image


@tool
async def browse_web(
    url: str,
    question: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Mở trang web và đọc nội dung. Có thể hỏi câu hỏi về trang.

    Args:
        url: URL trang web cần mở
        question: câu hỏi về nội dung trang (optional)
    """
    try:
        result = await navigate_and_extract(url)
    except Exception as e:
        return f"Không thể mở trang: {e}"

    title = result["title"]
    text = result["text"]

    if question:
        from llm.gateway import get_llm
        llm = get_llm("gemini-2.0-flash")
        resp = await llm.ainvoke(
            f"Dựa vào nội dung trang web sau, trả lời câu hỏi bằng tiếng Việt.\n\n"
            f"Tiêu đề: {title}\nNội dung:\n{text[:3000]}\n\n"
            f"Câu hỏi: {question}"
        )
        return f"🌐 {title}\n\n{resp.content}"

    if not text:
        return f"🌐 {title} — Không trích xuất được nội dung text."

    return f"🌐 {title}\n\n{text[:2000]}"


@tool
async def browse_click(
    url: str,
    selector: str,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Mở trang web, click vào element, đọc kết quả.

    Args:
        url: URL trang web
        selector: CSS selector của element cần click (ví dụ: "button.submit")
    """
    try:
        result = await click_and_extract(url, selector)
    except Exception as e:
        return f"Không thể click: {e}"

    return f"🌐 {result['title']}\n\n{result['text'][:2000]}"


@tool
async def browse_fill(
    url: str,
    fields: str,
    submit_selector: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Mở trang web, điền form, submit.

    Args:
        url: URL trang web có form
        fields: JSON string {"css_selector": "value"} cho các field cần điền
        submit_selector: CSS selector của nút submit (optional)
    """
    import json
    try:
        field_dict = json.loads(fields)
    except json.JSONDecodeError:
        return "fields phải là JSON: {\"selector\": \"value\"}"

    try:
        result = await fill_and_submit(url, field_dict, submit_selector)
    except Exception as e:
        return f"Không thể điền form: {e}"

    return f"🌐 {result['title']}\n\n{result['text'][:2000]}"


@tool
async def browse_screenshot(
    url: str,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Chụp screenshot trang web và phân tích bằng AI.

    Args:
        url: URL trang web cần chụp
    """
    try:
        b64 = await screenshot_page(url)
    except Exception as e:
        return f"Không thể chụp screenshot: {e}"

    import base64
    img_bytes = base64.b64decode(b64)
    analysis = await analyze_image(
        img_bytes,
        "Mô tả chi tiết nội dung trang web trong screenshot này bằng tiếng Việt.",
        "image/png",
    )
    return f"📸 Screenshot analysis:\n{analysis}"
