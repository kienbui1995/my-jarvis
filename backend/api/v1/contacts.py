"""M55+M56: Contact CRM + Birthday/Anniversary."""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from core.pagination import PaginationParams, paginated_response
from db.models import Contact
from services.crud import CRUDService

router = APIRouter()
svc = CRUDService(Contact)


class ContactCreate(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None
    relationship: str | None = None
    birthday: date | None = None
    anniversary: date | None = None
    company: str | None = None
    notes: str | None = None


@router.get("/")
async def list_contacts(p: PaginationParams = Depends(), relationship: str | None = None, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    filters = {"relationship": relationship} if relationship else None
    items, total = await svc.list(db, user_id, page=p.page, page_size=p.page_size, filters=filters)
    return paginated_response(items, total, p)


@router.post("/")
async def create_contact(body: ContactCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await svc.create(db, user_id, **body.model_dump(exclude_none=True))


@router.get("/{contact_id}")
async def get_contact(contact_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await svc.get(db, user_id, contact_id)


@router.patch("/{contact_id}")
async def update_contact(contact_id: str, body: ContactCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await svc.update(db, user_id, contact_id, **body.model_dump(exclude_none=True))


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await svc.delete(db, user_id, contact_id)
    return {"ok": True}
