"""Finance tools — wired to DB, user_id auto-injected."""
from datetime import datetime
from typing import Annotated
from uuid import UUID

from langchain_core.tools import tool, InjectedToolArg
from sqlalchemy import select, func

from db.models import Expense
from db.session import async_session


@tool
async def expense_log(
    amount: float, category: str, description: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Ghi chi tiêu. Args: amount (VND), category, description (optional)."""
    async with async_session() as db:
        e = Expense(user_id=UUID(user_id), amount=amount, category=category, description=description)
        db.add(e)
        await db.commit()
        return f"💰 Đã ghi: {amount:,.0f}đ — {category}"


@tool
async def budget_check(
    category: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Kiểm tra chi tiêu tháng này. Args: category (optional)."""
    async with async_session() as db:
        q = select(func.sum(Expense.amount)).where(
            Expense.user_id == UUID(user_id),
            Expense.created_at >= datetime.utcnow().replace(day=1, hour=0, minute=0, second=0),
        )
        if category:
            q = q.where(Expense.category == category)
        result = await db.execute(q)
        total = result.scalar() or 0
        label = f" ({category})" if category else ""
        return f"💰 Chi tiêu tháng này{label}: {total:,.0f}đ"
