"""Memory browser API — list, search, delete user memories."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models.memory import Memory
from llm.embeddings import embed_text

router = APIRouter()


@router.get("/")
async def list_memories(
    memory_type: str = "",
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    uid = UUID(user_id)
    q = select(Memory).where(Memory.user_id == uid)
    if memory_type:
        q = q.where(Memory.memory_type == memory_type)
    q = q.order_by(Memory.created_at.desc()).offset(offset).limit(min(limit, 50))
    results = (await db.execute(q)).scalars().all()

    count_q = select(func.count()).select_from(Memory).where(Memory.user_id == uid)
    if memory_type:
        count_q = count_q.where(Memory.memory_type == memory_type)
    total = (await db.execute(count_q)).scalar() or 0

    return {
        "memories": [
            {
                "id": str(m.id),
                "type": m.memory_type,
                "content": m.content,
                "importance": m.importance,
                "metadata": m.metadata_,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in results
        ],
        "total": total,
    }


@router.get("/search")
async def search_memories(
    q: str,
    limit: int = 10,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query_embedding = await embed_text(q)

    results = (await db.execute(
        select(Memory)
        .where(Memory.user_id == UUID(user_id))
        .order_by(Memory.embedding.cosine_distance(query_embedding))
        .limit(min(limit, 20))
    )).scalars().all()

    return {
        "memories": [
            {
                "id": str(m.id),
                "type": m.memory_type,
                "content": m.content,
                "importance": m.importance,
                "metadata": m.metadata_,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in results
        ],
    }


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        uid = UUID(memory_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Not found")
    mem = await db.get(Memory, uid)
    if not mem or str(mem.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(mem)
    await db.commit()
    return {"deleted": True}
