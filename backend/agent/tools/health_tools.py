"""V11: Health & Personal Development tools (M70-M78)."""
from datetime import date, timedelta
from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedToolArg


@tool
async def log_health(metric: str, value: float, notes: str = "", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Ghi nhận sức khỏe: sleep (giờ), exercise (phút), water (ml), mood (1-10), weight (kg), steps. Args: metric, value, notes."""
    from db.session import async_session
    from db.models import HealthLog
    from uuid import UUID

    units = {"sleep": "hours", "exercise": "min", "water": "ml", "mood": "/10", "weight": "kg", "steps": "steps"}
    if metric not in units:
        return f"Metric '{metric}' không hỗ trợ. Dùng: {', '.join(units.keys())}"

    async with async_session() as db:
        db.add(HealthLog(user_id=UUID(user_id), metric=metric, value=value, unit=units[metric], notes=notes))
        await db.commit()
    return f"✅ Đã ghi: {metric} = {value}{units[metric]}"


@tool
async def health_summary(period: str = "week", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Tổng hợp sức khỏe tuần/tháng. Args: period (week|month)."""
    from db.session import async_session
    from db.models import HealthLog
    from sqlalchemy import select, func
    from uuid import UUID

    days = 7 if period == "week" else 30
    since = date.today() - timedelta(days=days)

    async with async_session() as db:
        rows = (await db.execute(
            select(HealthLog.metric, func.avg(HealthLog.value), func.count()).where(
                HealthLog.user_id == UUID(user_id), HealthLog.log_date >= since
            ).group_by(HealthLog.metric)
        )).all()

    if not rows:
        return f"Chưa có dữ liệu sức khỏe trong {days} ngày qua."
    return f"📊 Sức khỏe {period}:\n" + "\n".join(f"  • {m}: avg {a:.1f} ({c} entries)" for m, a, c in rows)


@tool
async def review_flashcard(deck: str = "general", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Ôn tập flashcard theo SM-2. Args: deck."""
    from db.session import async_session
    from db.models import Flashcard
    from sqlalchemy import select
    from uuid import UUID

    async with async_session() as db:
        card = (await db.execute(
            select(Flashcard).where(
                Flashcard.user_id == UUID(user_id), Flashcard.deck == deck, Flashcard.next_review <= date.today()
            ).order_by(Flashcard.next_review).limit(1)
        )).scalar_one_or_none()

    if not card:
        return f"🎉 Không có thẻ nào cần ôn trong deck '{deck}'!"
    return f"📝 Flashcard (deck: {deck}):\n\n**Câu hỏi:** {card.front}\n\n||**Đáp án:** {card.back}||\n\nTrả lời: easy / good / hard / again"


@tool
async def answer_flashcard(card_id: str, quality: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Chấm điểm flashcard sau khi ôn. Args: card_id, quality (easy|good|hard|again)."""
    from db.session import async_session
    from db.models import Flashcard
    from uuid import UUID

    q_map = {"again": 0, "hard": 2, "good": 3, "easy": 5}
    q = q_map.get(quality, 3)

    async with async_session() as db:
        card = await db.get(Flashcard, UUID(card_id))
        if not card or card.user_id != UUID(user_id):
            return "Không tìm thấy thẻ."

        # SM-2 algorithm
        if q < 3:
            card.repetitions = 0
            card.interval = 1
        else:
            if card.repetitions == 0:
                card.interval = 1
            elif card.repetitions == 1:
                card.interval = 6
            else:
                card.interval = int(card.interval * card.ease_factor)
            card.repetitions += 1

        card.ease_factor = max(1.3, card.ease_factor + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        card.next_review = date.today() + timedelta(days=card.interval)
        card.last_reviewed = date.today()
        await db.commit()

    return f"✅ Next review: {card.next_review} (interval: {card.interval}d)"


@tool
async def add_book_note(title: str, highlight: str = "", summary: str = "", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Ghi chú sách — thêm highlight hoặc tóm tắt. Args: title, highlight, summary."""
    from db.session import async_session
    from db.models import BookNote
    from sqlalchemy import select
    from uuid import UUID

    async with async_session() as db:
        book = (await db.execute(
            select(BookNote).where(BookNote.user_id == UUID(user_id), BookNote.title.ilike(f"%{title}%"))
        )).scalar_one_or_none()

        if not book:
            book = BookNote(user_id=UUID(user_id), title=title, status="reading")
            db.add(book)

        if highlight:
            hl = book.highlights or []
            hl.append({"text": highlight})
            book.highlights = hl
        if summary:
            book.summary = summary
        await db.commit()

    return f"📚 Đã ghi chú cho '{book.title}'" + (f" — highlight #{len(book.highlights or [])}" if highlight else "")


@tool
async def nutrition_lookup(food: str, user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Tra cứu calories thức ăn Việt Nam. Args: food (ví dụ: 'phở bò', 'cơm tấm')."""
    from llm.gateway import get_llm

    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Tra cứu dinh dưỡng món ăn Việt Nam: {food}\n\n"
        "Trả về ngắn gọn: Calories, Protein, Carbs, Fat cho 1 phần ăn trung bình. "
        "Dùng dữ liệu thực tế cho thức ăn Việt Nam."
    )
    return resp.content


@tool
async def fitness_suggest(goal: str = "general", user_id: Annotated[str, InjectedToolArg] = "") -> str:
    """Gợi ý bài tập phù hợp. Args: goal (general|weight_loss|muscle|cardio|flexibility)."""
    from llm.gateway import get_llm

    llm = get_llm("gemini-2.0-flash")
    resp = await llm.ainvoke(
        f"Gợi ý bài tập cho mục tiêu: {goal}.\n"
        "Cho 5 bài tập, mỗi bài: tên, số set x rep, thời gian, mức độ. "
        "Phù hợp người Việt Nam, có thể tập tại nhà."
    )
    return resp.content
