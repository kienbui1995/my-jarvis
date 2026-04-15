"""M67: Home Assistant IoT + M68: VN Banking + M69: ZaloPay/MoMo."""
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg


@tool
async def home_control(entity: str, action: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Điều khiển thiết bị nhà thông minh qua Home Assistant. Args: entity (light.bedroom, climate.living_room...), action (turn_on|turn_off|toggle|set_temperature:25)."""
    import httpx
    from core.config import settings

    if not settings.HOME_ASSISTANT_URL or not settings.HOME_ASSISTANT_TOKEN:
        return "⚠️ Chưa cấu hình Home Assistant. Thêm HOME_ASSISTANT_URL và HOME_ASSISTANT_TOKEN trong Settings."

    headers = {"Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}"}
    base = settings.HOME_ASSISTANT_URL.rstrip("/")

    async with httpx.AsyncClient() as client:
        if action.startswith("set_temperature:"):
            temp = float(action.split(":")[1])
            r = await client.post(f"{base}/api/services/climate/set_temperature", json={"entity_id": entity, "temperature": temp}, headers=headers)
        elif action in ("turn_on", "turn_off", "toggle"):
            domain = entity.split(".")[0]
            r = await client.post(f"{base}/api/services/{domain}/{action}", json={"entity_id": entity}, headers=headers)
        else:
            return f"Action '{action}' không hỗ trợ. Dùng: turn_on, turn_off, toggle, set_temperature:25"

    return f"✅ {entity} → {action}" if r.status_code == 200 else f"❌ Lỗi: {r.status_code}"


@tool
async def home_status(user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Xem trạng thái các thiết bị nhà thông minh."""
    import httpx
    from core.config import settings

    if not settings.HOME_ASSISTANT_URL or not settings.HOME_ASSISTANT_TOKEN:
        return "⚠️ Chưa cấu hình Home Assistant."

    headers = {"Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.HOME_ASSISTANT_URL.rstrip('/')}/api/states", headers=headers)
        if r.status_code != 200:
            return f"❌ Lỗi kết nối Home Assistant: {r.status_code}"
        states = r.json()

    # Filter to common entities
    relevant = [s for s in states if s["entity_id"].split(".")[0] in ("light", "climate", "switch", "sensor", "lock")][:15]
    if not relevant:
        return "Không tìm thấy thiết bị nào."
    return "\n".join(f"{'💡' if 'light' in s['entity_id'] else '🌡️' if 'climate' in s['entity_id'] else '🔌'} {s['attributes'].get('friendly_name', s['entity_id'])}: {s['state']}" for s in relevant)


@tool
async def parse_bank_transaction(message: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Phân tích tin nhắn ngân hàng VN (SMS/email) → ghi chi tiêu. Args: message (nội dung SMS/email)."""
    from llm.gateway import get_llm
    import json

    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Phân tích tin nhắn ngân hàng Việt Nam sau:\n\n{message}\n\n"
        'Trả về JSON: {"bank": "", "type": "credit|debit", "amount": 0, "balance": 0, "description": "", "time": ""}\n'
        "Nếu không phải tin nhắn ngân hàng, trả về null."
    )

    try:
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
        if not data:
            return "Không phải tin nhắn ngân hàng."

        # Auto-log expense if debit
        if data.get("type") == "debit" and data.get("amount"):
            from db.session import async_session
            from db.models import Expense
            from uuid import UUID
            async with async_session() as db:
                db.add(Expense(user_id=UUID(user_id), amount=data["amount"], category="bank_transfer", description=f"{data.get('bank','')}: {data.get('description','')}"))
                await db.commit()

        icon = "📤" if data.get("type") == "debit" else "📥"
        return f"{icon} {data.get('bank','')}: {data.get('type','')} {data.get('amount',0):,.0f}đ\n💰 Số dư: {data.get('balance',0):,.0f}đ\n📝 {data.get('description','')}"
    except Exception:
        return f"Phân tích: {resp.content}"


@tool
async def parse_epayment(message: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Phân tích thông báo ZaloPay/MoMo/VNPay → ghi chi tiêu. Args: message."""
    from llm.gateway import get_llm
    import json

    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Phân tích thông báo thanh toán điện tử VN:\n\n{message}\n\n"
        'Trả về JSON: {"platform": "zalopay|momo|vnpay", "type": "payment|receive|topup", "amount": 0, "merchant": "", "time": ""}\n'
        "Nếu không phải thông báo thanh toán, trả về null."
    )

    try:
        data = json.loads(resp.content.strip().removeprefix("```json").removesuffix("```").strip())
        if not data:
            return "Không phải thông báo thanh toán."

        if data.get("type") == "payment" and data.get("amount"):
            from db.session import async_session
            from db.models import Expense
            from uuid import UUID
            async with async_session() as db:
                db.add(Expense(user_id=UUID(user_id), amount=data["amount"], category="epayment", description=f"{data.get('platform','')}: {data.get('merchant','')}"))
                await db.commit()

        icon = "💸" if data.get("type") == "payment" else "💰"
        return f"{icon} {data.get('platform','')}: {data.get('amount',0):,.0f}đ → {data.get('merchant','')}"
    except Exception:
        return f"Phân tích: {resp.content}"
