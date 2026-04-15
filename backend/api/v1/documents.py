"""M57: Document Vault — encrypted storage for important documents."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from core.pagination import PaginationParams, paginated_response
from db.models import Document
from services.crud import CRUDService

router = APIRouter()
svc = CRUDService(Document)


class DocCreate(BaseModel):
    name: str
    doc_type: str  # id_card, passport, insurance, contract, certificate
    file_key: str | None = None
    doc_number: str | None = None
    issuer: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None
    notes: str | None = None


@router.get("/")
async def list_docs(p: PaginationParams = Depends(), doc_type: str | None = None, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    filters = {"doc_type": doc_type} if doc_type else None
    items, total = await svc.list(db, user_id, page=p.page, page_size=p.page_size, filters=filters)
    return paginated_response(items, total, p)


@router.post("/")
async def create_doc(body: DocCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await svc.create(db, user_id, **body.model_dump(exclude_none=True))


@router.get("/{doc_id}")
async def get_doc(doc_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await svc.get(db, user_id, doc_id)


@router.delete("/{doc_id}")
async def delete_doc(doc_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await svc.delete(db, user_id, doc_id)
    return {"ok": True}
