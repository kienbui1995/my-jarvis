"""V12 models — Goals & Decision Journal."""
from datetime import date

from sqlalchemy import Boolean, Date, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, UserOwnedMixin


# ── M86: Goal System OKR ──

class Goal(UserOwnedMixin, Base):
    __tablename__ = "goals"

    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    goal_type: Mapped[str] = mapped_column(String(20), default="objective")  # objective, key_result
    parent_id: Mapped[str | None] = mapped_column(String(36))  # FK to parent goal (OKR hierarchy)
    target_value: Mapped[float | None] = mapped_column(Float)
    current_value: Mapped[float] = mapped_column(Float, default=0)
    unit: Mapped[str | None] = mapped_column(String(50))
    deadline: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, completed, abandoned
    tags: Mapped[dict | None] = mapped_column(JSONB, default=list)


# ── M87: Decision Journal ──

class Decision(UserOwnedMixin, Base):
    __tablename__ = "decisions"

    title: Mapped[str] = mapped_column(String(500))
    context: Mapped[str | None] = mapped_column(Text)  # What situation led to this decision
    options: Mapped[dict | None] = mapped_column(JSONB, default=list)  # [{option, pros, cons}]
    chosen: Mapped[str | None] = mapped_column(Text)  # What was decided
    reasoning: Mapped[str | None] = mapped_column(Text)  # Why
    outcome: Mapped[str | None] = mapped_column(Text)  # What happened (filled later)
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5 retrospective
    review_date: Mapped[date | None] = mapped_column(Date)  # When to review outcome
