"""Foundation usage examples — how V8-V14 modules should be built.

This file is documentation only, not imported anywhere.
Delete after team is familiar with patterns.
"""

# ═══════════════════════════════════════════════════════════════
# EXAMPLE 1: New DB Model (e.g., Contact for V9)
# Before foundation: 15 lines of boilerplate
# After foundation: 5 lines
# ═══════════════════════════════════════════════════════════════

# --- db/models/contact.py ---
"""
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, UserOwnedMixin


class Contact(UserOwnedMixin, Base):
    __tablename__ = "contacts"

    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    relationship: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    preferences: Mapped[dict | None] = mapped_column(JSONB, default={})

# That's it! id, user_id, created_at, updated_at are automatic.
"""


# ═══════════════════════════════════════════════════════════════
# EXAMPLE 2: New API with CRUD + Pagination (e.g., Contacts API)
# Before foundation: 60+ lines
# After foundation: 20 lines
# ═══════════════════════════════════════════════════════════════

# --- api/v1/contacts.py ---
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from core.pagination import PaginationParams, paginated_response
from db.models.contact import Contact
from services.crud import CRUDService

router = APIRouter()
svc = CRUDService(Contact)


class ContactCreate(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    relationship: str | None = None


@router.get("/")
async def list_contacts(p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await svc.list(db, user_id, page=p.page, page_size=p.page_size)
    return paginated_response(items, total, p)


@router.post("/")
async def create_contact(body: ContactCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await svc.create(db, user_id, **body.model_dump())


@router.patch("/{contact_id}")
async def update_contact(contact_id: str, body: ContactCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await svc.update(db, user_id, contact_id, **body.model_dump(exclude_none=True))


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await svc.delete(db, user_id, contact_id)
    return {"ok": True}

# Auto-registered! No need to edit main.py. Prefix: /api/v1/contacts
"""


# ═══════════════════════════════════════════════════════════════
# EXAMPLE 3: New Agent Tool
# Just create file, use @tool decorator. Auto-discovered.
# ═══════════════════════════════════════════════════════════════

# --- agent/tools/contact_tools.py ---
"""
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg

@tool
async def contact_search(
    query: str,
    user_id: Annotated[str, InjectedToolArg],
) -> str:
    \"\"\"Tìm kiếm liên hệ theo tên hoặc mối quan hệ.\"\"\"
    from db.session import async_session
    from db.models.contact import Contact
    from sqlalchemy import select, or_
    from uuid import UUID

    async with async_session() as db:
        results = (await db.execute(
            select(Contact).where(
                Contact.user_id == UUID(user_id),
                or_(Contact.name.ilike(f"%{query}%"), Contact.relationship.ilike(f"%{query}%"))
            ).limit(10)
        )).scalars().all()
        if not results:
            return "Không tìm thấy liên hệ nào."
        return "\\n".join(f"- {c.name} ({c.relationship}): {c.phone}" for c in results)

# Auto-discovered! No need to edit agent/tools/__init__.py
"""


# ═══════════════════════════════════════════════════════════════
# EXAMPLE 4: New Proactive Trigger
# Already had good pattern — just create file in services/handlers/
# ═══════════════════════════════════════════════════════════════

# --- services/handlers/birthday_reminder.py ---
"""
from services.trigger_engine import TriggerHandler, register_handler

@register_handler
class BirthdayReminderHandler(TriggerHandler):
    TRIGGER_TYPE = "birthday_reminder"
    LISTENS_TO = ["cron.check_birthdays"]

    async def should_fire(self, trigger, event, db) -> bool:
        # Check if any contact has birthday today
        ...

    async def build_message(self, trigger, event, db) -> str:
        return "🎂 Hôm nay là sinh nhật của Alice! Gợi ý quà: ..."

# Auto-registered via @register_handler decorator
"""
