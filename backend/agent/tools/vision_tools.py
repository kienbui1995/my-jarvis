"""Vision tools — image analysis and OCR via Gemini multimodal."""
from typing import Annotated

from langchain_core.tools import InjectedToolArg, tool

from services.storage import get_file_bytes
from services.vision import analyze_image, ocr_document


@tool
async def analyze_file(
    file_key: str,
    question: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Phân tích ảnh/file đã upload. Args: file_key (từ upload), question (câu hỏi, optional).

    Ví dụ: analyze_file("uploads/abc123.jpg", "Hóa đơn này tổng bao nhiêu?")
    """
    try:
        data = get_file_bytes(file_key)
    except Exception:
        return f"Không tìm thấy file: {file_key}"

    ext = file_key.rsplit(".", 1)[-1].lower() if "." in file_key else ""
    ct_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
              "webp": "image/webp", "gif": "image/gif"}
    content_type = ct_map.get(ext, "image/jpeg")

    prompt = question if question else "Mô tả chi tiết nội dung ảnh này bằng tiếng Việt."
    result = await analyze_image(data, prompt, content_type)
    return f"🖼 Phân tích: {result}"


@tool
async def ocr_file(
    file_key: str,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """OCR — trích xuất text từ ảnh (hóa đơn, receipt, screenshot). Args: file_key."""
    try:
        data = get_file_bytes(file_key)
    except Exception:
        return f"Không tìm thấy file: {file_key}"

    ext = file_key.rsplit(".", 1)[-1].lower() if "." in file_key else ""
    ct_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
              "webp": "image/webp", "gif": "image/gif"}
    content_type = ct_map.get(ext, "image/jpeg")

    result = await ocr_document(data, content_type)
    return f"📝 OCR kết quả:\n{result}"
