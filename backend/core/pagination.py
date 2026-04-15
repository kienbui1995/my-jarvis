"""Pagination utilities for API endpoints.

Usage:
    from core.pagination import PaginationParams, paginated_response

    @router.get("/contacts")
    async def list_contacts(
        p: PaginationParams = Depends(),
        user_id: str = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ):
        items, total = await contact_svc.list(db, user_id, page=p.page, page_size=p.page_size)
        return paginated_response(items, total, p, serialize=lambda c: {"id": str(c.id), "name": c.name})
"""
from typing import Any, Callable

from fastapi import Query


class PaginationParams:
    """FastAPI dependency for pagination query params."""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size


def paginated_response(
    items: list,
    total: int,
    params: PaginationParams,
    serialize: Callable[[Any], dict] | None = None,
) -> dict:
    """Standard paginated response envelope."""
    data = [serialize(i) for i in items] if serialize else [_auto_serialize(i) for i in items]
    return {
        "data": data,
        "meta": {
            "page": params.page,
            "page_size": params.page_size,
            "total": total,
            "pages": (total + params.page_size - 1) // params.page_size if params.page_size else 0,
        },
    }


def _auto_serialize(obj: Any) -> dict:
    """Auto-serialize SQLAlchemy model to dict (non-relationship columns only)."""
    if hasattr(obj, "__table__"):
        d = {}
        for col in obj.__table__.columns:
            val = getattr(obj, col.key, None)
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            elif hasattr(val, "hex"):  # UUID
                val = str(val)
            d[col.key] = val
        return d
    return obj
