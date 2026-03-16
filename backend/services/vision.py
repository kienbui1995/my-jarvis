"""Vision — image/document analysis via Gemini multimodal through LiteLLM."""
import base64
import logging

from openai import AsyncOpenAI

from core.config import settings

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(
    api_key=settings.LITELLM_API_KEY, base_url=settings.LITELLM_BASE_URL
)

# Map content types to media types for base64 encoding
_MEDIA_TYPES = {
    "image/jpeg": "image/jpeg",
    "image/png": "image/png",
    "image/webp": "image/webp",
    "image/gif": "image/gif",
}


async def analyze_image(
    image_bytes: bytes,
    prompt: str = "Mô tả chi tiết nội dung ảnh này bằng tiếng Việt.",
    content_type: str = "image/jpeg",
) -> str:
    """Analyze an image using Gemini vision via LiteLLM proxy.

    Returns the model's text analysis of the image.
    """
    media_type = _MEDIA_TYPES.get(content_type, "image/jpeg")
    b64 = base64.b64encode(image_bytes).decode()

    response = await _client.chat.completions.create(
        model="gemini/gemini-2.0-flash",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{b64}",
                        },
                    },
                ],
            }
        ],
        max_tokens=1000,
    )

    return response.choices[0].message.content or ""


async def ocr_document(
    image_bytes: bytes,
    content_type: str = "image/jpeg",
) -> str:
    """Extract text from image (OCR) using Gemini vision."""
    return await analyze_image(
        image_bytes,
        prompt=(
            "Trích xuất TOÀN BỘ text trong ảnh này. "
            "Giữ nguyên format, bao gồm số, ngày, tên. "
            "Nếu là hóa đơn/receipt, liệt kê các mục và tổng tiền."
        ),
        content_type=content_type,
    )
