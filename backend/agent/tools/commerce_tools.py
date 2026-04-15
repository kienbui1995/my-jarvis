"""M64: E-commerce Tracking + M66: Grab Integration."""
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg


@tool
async def track_order(order_id: str, platform: str = "auto", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Tra cứu đơn hàng Shopee/Lazada/Tiki. Args: order_id, platform (shopee|lazada|tiki|auto)."""
    from llm.gateway import get_llm

    # E-commerce platforms in VN don't have public tracking APIs
    # Use LLM to guide user on how to check
    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Người dùng muốn tra đơn hàng #{order_id} trên {platform}.\n"
        "Hướng dẫn ngắn gọn cách kiểm tra trạng thái đơn hàng trên app/web. "
        "Nếu biết format mã đơn, đoán platform. Gợi ý link tracking nếu có."
    )
    return resp.content


@tool
async def grab_estimate(pickup: str, dropoff: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Ước tính giá Grab từ A đến B. Args: pickup, dropoff."""
    from llm.gateway import get_llm

    # Grab doesn't have public fare estimation API
    # Use LLM with knowledge of VN pricing
    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Ước tính giá Grab từ '{pickup}' đến '{dropoff}' tại Việt Nam.\n"
        "Cho giá ước tính GrabBike và GrabCar (VND). "
        "Dựa trên khoảng cách ước tính và giá trung bình hiện tại. "
        "Gợi ý giờ đi để tránh surge pricing."
    )
    return resp.content
