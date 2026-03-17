"""Note/memo tools — personal notes stored via memory system (pgvector)."""
from typing import Annotated
from uuid import UUID

from langchain_core.tools import InjectedToolArg, tool
from sqlalchemy import select

from db.models.memory import Memory
from db.session import async_session
from llm.embeddings import embed_text


@tool
async def note_save(
    content: str,
    title: str = "",
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Lưu ghi chú/memo cá nhân.

    Args:
        content: nội dung ghi chú
        title: tiêu đề (tùy chọn)
    """
    full_text = f"{title}: {content}" if title else content
    embedding = await embed_text(full_text)

    async with async_session() as db:
        note = Memory(
            user_id=UUID(user_id),
            memory_type="note",
            content=full_text,
            embedding=embedding,
            importance=0.7,
            metadata={"title": title} if title else {},
        )
        db.add(note)
        await db.commit()

    label = f' "{title}"' if title else ""
    return f"📝 Đã lưu ghi chú{label}."


@tool
async def note_search(
    query: str,
    limit: int = 5,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Tìm kiếm trong ghi chú cá nhân.

    Args:
        query: từ khóa tìm kiếm
        limit: số kết quả tối đa (mặc định 5)
    """
    query_embedding = await embed_text(query)

    async with async_session() as db:
        results = (await db.execute(
            select(Memory)
            .where(Memory.user_id == UUID(user_id), Memory.memory_type == "note")
            .order_by(Memory.embedding.cosine_distance(query_embedding))
            .limit(min(limit, 10))
        )).scalars().all()

    if not results:
        return "📝 Không tìm thấy ghi chú nào."

    lines = [f"📝 Tìm thấy {len(results)} ghi chú:"]
    for i, note in enumerate(results, 1):
        title = note.metadata.get("title", "") if note.metadata else ""
        preview = note.content[:100]
        if title:
            lines.append(f"{i}. **{title}**: {preview}")
        else:
            lines.append(f"{i}. {preview}")
    return "\n".join(lines)


@tool
async def note_list(
    limit: int = 10,
    user_id: Annotated[str, InjectedToolArg] = "",
) -> str:
    """Liệt kê ghi chú gần đây.

    Args:
        limit: số ghi chú tối đa (mặc định 10)
    """
    async with async_session() as db:
        results = (await db.execute(
            select(Memory)
            .where(Memory.user_id == UUID(user_id), Memory.memory_type == "note")
            .order_by(Memory.created_at.desc())
            .limit(min(limit, 20))
        )).scalars().all()

    if not results:
        return "📝 Chưa có ghi chú nào."

    lines = [f"📝 {len(results)} ghi chú gần đây:"]
    for i, note in enumerate(results, 1):
        title = note.metadata.get("title", "") if note.metadata else ""
        preview = note.content[:80]
        date = note.created_at.strftime("%d/%m") if note.created_at else ""
        if title:
            lines.append(f"{i}. [{date}] **{title}**: {preview}")
        else:
            lines.append(f"{i}. [{date}] {preview}")
    return "\n".join(lines)
