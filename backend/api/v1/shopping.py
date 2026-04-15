"""M59: Shopping Lists."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from core.pagination import PaginationParams, paginated_response
from db.models import ShoppingItem, ShoppingList
from services.crud import CRUDService

router = APIRouter()
list_svc = CRUDService(ShoppingList)


class ListCreate(BaseModel):
    name: str = "Danh sách mua sắm"


class ItemCreate(BaseModel):
    name: str
    quantity: int = 1
    unit: str | None = None


@router.get("/")
async def get_lists(p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await list_svc.list(db, user_id, page=p.page, page_size=p.page_size)
    return paginated_response(items, total, p)


@router.post("/")
async def create_list(body: ListCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await list_svc.create(db, user_id, name=body.name)


@router.get("/{list_id}/items")
async def get_items(list_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    sl = await list_svc.get(db, user_id, list_id)
    items = (await db.execute(select(ShoppingItem).where(ShoppingItem.list_id == sl.id))).scalars().all()
    return [{"id": str(i.id), "name": i.name, "quantity": i.quantity, "unit": i.unit, "checked": i.checked} for i in items]


@router.post("/{list_id}/items")
async def add_item(list_id: str, body: ItemCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    sl = await list_svc.get(db, user_id, list_id)
    item = ShoppingItem(list_id=sl.id, name=body.name, quantity=body.quantity, unit=body.unit)
    db.add(item)
    await db.commit()
    return {"id": str(item.id), "name": item.name}


@router.patch("/{list_id}/items/{item_id}")
async def toggle_item(list_id: str, item_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await list_svc.get(db, user_id, list_id)  # verify ownership
    item = await db.get(ShoppingItem, UUID(item_id))
    if not item or item.list_id != UUID(list_id):
        raise HTTPException(404)
    item.checked = not item.checked
    await db.commit()
    return {"checked": item.checked}
