"""Generic async CRUD service — eliminates boilerplate for simple domain models.

Usage:
    from services.crud import CRUDService
    from db.models import Contact

    contact_svc = CRUDService(Contact)

    # In API endpoint:
    items, total = await contact_svc.list(db, user_id, page=1, page_size=20)
    item = await contact_svc.create(db, user_id, name="Alice", phone="0901234567")
    item = await contact_svc.get(db, user_id, item_id)
    item = await contact_svc.update(db, user_id, item_id, name="Bob")
    await contact_svc.delete(db, user_id, item_id)
"""
from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class CRUDService:
    """Generic CRUD for user-owned SQLAlchemy models."""

    def __init__(self, model: type):
        self.model = model

    async def create(self, db: AsyncSession, user_id: str, **data: Any):
        obj = self.model(user_id=UUID(user_id), **data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def get(self, db: AsyncSession, user_id: str, item_id: str):
        obj = await db.get(self.model, UUID(item_id))
        if not obj or obj.user_id != UUID(user_id):
            raise HTTPException(404, "Not found")
        return obj

    async def list(
        self, db: AsyncSession, user_id: str,
        page: int = 1, page_size: int = 20,
        order_by: str = "created_at", desc: bool = True,
        filters: dict | None = None,
    ) -> tuple[list, int]:
        """Return (items, total_count)."""
        uid = UUID(user_id)
        q = select(self.model).where(self.model.user_id == uid)

        # Apply filters
        if filters:
            for key, val in filters.items():
                if hasattr(self.model, key) and val is not None:
                    q = q.where(getattr(self.model, key) == val)

        # Count
        count_q = select(func.count()).select_from(q.subquery())
        total = (await db.execute(count_q)).scalar() or 0

        # Order + paginate
        col = getattr(self.model, order_by, self.model.created_at)
        q = q.order_by(col.desc() if desc else col.asc())
        q = q.offset((page - 1) * page_size).limit(page_size)

        items = (await db.execute(q)).scalars().all()
        return items, total

    async def update(self, db: AsyncSession, user_id: str, item_id: str, **data: Any):
        clean = {k: v for k, v in data.items() if v is not None}
        if not clean:
            return await self.get(db, user_id, item_id)

        result = await db.execute(
            update(self.model)
            .where(self.model.id == UUID(item_id), self.model.user_id == UUID(user_id))
            .values(**clean)
            .returning(self.model.id)
        )
        if not result.first():
            raise HTTPException(404, "Not found")
        await db.commit()
        return await self.get(db, user_id, item_id)

    async def delete(self, db: AsyncSession, user_id: str, item_id: str) -> bool:
        result = await db.execute(
            delete(self.model)
            .where(self.model.id == UUID(item_id), self.model.user_id == UUID(user_id))
        )
        await db.commit()
        return result.rowcount > 0
