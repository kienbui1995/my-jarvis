"""V9 Life tools — contacts, bills, subscriptions, documents, shopping, travel, receipt OCR."""
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg


@tool
async def receipt_ocr(file_key: str, user_id: Annotated[str, InjectedToolArg]) -> str:
    """Phân tích hóa đơn/receipt từ ảnh → tự động ghi chi tiêu. Args: file_key (MinIO key của ảnh)."""
    from services.vision import analyze_image
    from db.session import async_session
    from db.models import Expense
    from uuid import UUID
    import json

    analysis = await analyze_image(file_key, "Trích xuất thông tin hóa đơn: tên cửa hàng, tổng tiền (VND), danh mục (ăn uống/mua sắm/di chuyển/khác). Trả về JSON: {\"store\": \"\", \"amount\": 0, \"category\": \"\"}")
    try:
        data = json.loads(analysis.strip().removeprefix("```json").removesuffix("```").strip())
    except Exception:
        return f"Phân tích hóa đơn: {analysis}"

    amount = data.get("amount", 0)
    category = data.get("category", "khác")
    store = data.get("store", "")

    async with async_session() as db:
        db.add(Expense(user_id=UUID(user_id), amount=amount, category=category, description=f"OCR: {store}"))
        await db.commit()

    return f"📝 OCR: {store} — {amount:,.0f}đ ({category}). Đã ghi chi tiêu."


@tool
async def contact_search(query: str, user_id: Annotated[str, InjectedToolArg]) -> str:
    """Tìm kiếm liên hệ theo tên, mối quan hệ, hoặc công ty. Args: query."""
    from db.session import async_session
    from db.models import Contact
    from sqlalchemy import select, or_
    from uuid import UUID

    async with async_session() as db:
        results = (await db.execute(
            select(Contact).where(
                Contact.user_id == UUID(user_id),
                or_(Contact.name.ilike(f"%{query}%"), Contact.relationship.ilike(f"%{query}%"), Contact.company.ilike(f"%{query}%"))
            ).limit(10)
        )).scalars().all()

    if not results:
        return "Không tìm thấy liên hệ nào."
    return "\n".join(f"- {c.name} ({c.relationship or '?'}){f' — {c.phone}' if c.phone else ''}{f' 🎂 {c.birthday}' if c.birthday else ''}" for c in results)


@tool
async def plan_trip(destination: str, days: int, user_id: Annotated[str, InjectedToolArg]) -> str:
    """Lên kế hoạch chuyến đi: gợi ý lịch trình, packing list, budget. Args: destination, days."""
    from llm.gateway import get_llm

    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Lên kế hoạch đi {destination} trong {days} ngày cho người Việt Nam.\n\n"
        "Format:\n## Lịch trình\n## Packing list\n## Budget ước tính (VND)\n## Tips\n\nNgắn gọn, thực tế."
    )
    return resp.content


@tool
async def document_search(query: str, user_id: Annotated[str, InjectedToolArg]) -> str:
    """Tìm giấy tờ quan trọng (CCCD, passport, bảo hiểm...). Args: query."""
    from db.session import async_session
    from db.models import Document
    from sqlalchemy import select, or_
    from uuid import UUID

    async with async_session() as db:
        results = (await db.execute(
            select(Document).where(
                Document.user_id == UUID(user_id),
                or_(Document.name.ilike(f"%{query}%"), Document.doc_type.ilike(f"%{query}%"))
            ).limit(10)
        )).scalars().all()

    if not results:
        return "Không tìm thấy giấy tờ nào."
    return "\n".join(
        f"- {d.name} ({d.doc_type}){f' — Số: {d.doc_number}' if d.doc_number else ''}{f' — HSD: {d.expiry_date}' if d.expiry_date else ''}"
        for d in results
    )
