"""V11: Health & Wellness APIs — health logs, medications, flashcards, books."""
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from core.pagination import PaginationParams, paginated_response
from db.models import BookNote, Flashcard, HealthLog, Medication
from services.crud import CRUDService

router = APIRouter()
health_svc = CRUDService(HealthLog)
med_svc = CRUDService(Medication)
card_svc = CRUDService(Flashcard)
book_svc = CRUDService(BookNote)


# ── Health Logs ──

class HealthLogCreate(BaseModel):
    metric: str
    value: float
    unit: str = ""
    log_date: date = None
    notes: str | None = None


@router.get("/logs")
async def list_health_logs(metric: str | None = None, p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    filters = {"metric": metric} if metric else None
    items, total = await health_svc.list(db, user_id, page=p.page, page_size=p.page_size, filters=filters)
    return paginated_response(items, total, p)


@router.post("/logs")
async def create_health_log(body: HealthLogCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await health_svc.create(db, user_id, **body.model_dump(exclude_none=True))


# ── Medications ──

class MedCreate(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str = "daily"
    times: list[str] = []
    start_date: date | None = None
    end_date: date | None = None


@router.get("/medications")
async def list_meds(p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await med_svc.list(db, user_id, page=p.page, page_size=p.page_size, filters={"active": True})
    return paginated_response(items, total, p)


@router.post("/medications")
async def create_med(body: MedCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await med_svc.create(db, user_id, **body.model_dump(exclude_none=True))


@router.delete("/medications/{med_id}")
async def delete_med(med_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await med_svc.delete(db, user_id, med_id)
    return {"ok": True}


# ── Flashcards ──

@router.get("/flashcards")
async def list_flashcards(deck: str = "general", p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    items, total = await card_svc.list(db, user_id, page=p.page, page_size=p.page_size, filters={"deck": deck})
    return paginated_response(items, total, p)


class CardCreate(BaseModel):
    front: str
    back: str
    deck: str = "general"


@router.post("/flashcards")
async def create_flashcard(body: CardCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await card_svc.create(db, user_id, **body.model_dump())


# ── Books ──

@router.get("/books")
async def list_books(status: str | None = None, p: PaginationParams = Depends(), user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    filters = {"status": status} if status else None
    items, total = await book_svc.list(db, user_id, page=p.page, page_size=p.page_size, filters=filters)
    return paginated_response(items, total, p)


@router.post("/books")
async def create_book(body: dict, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    return await book_svc.create(db, user_id, **body)
