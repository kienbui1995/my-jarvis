"""V11 models — Health & Personal Development."""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, UserOwnedMixin


# ── M70: Health Tracking ──

class HealthLog(UserOwnedMixin, Base):
    __tablename__ = "health_logs"

    log_date: Mapped[date] = mapped_column(Date, default=date.today)
    metric: Mapped[str] = mapped_column(String(50))  # sleep, exercise, water, mood, weight, steps
    value: Mapped[float] = mapped_column(Float)  # hours, minutes, ml, 1-10, kg, count
    unit: Mapped[str] = mapped_column(String(20), default="")
    notes: Mapped[str | None] = mapped_column(Text)


# ── M71: Medication Reminders ──

class Medication(UserOwnedMixin, Base):
    __tablename__ = "medications"

    name: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[str | None] = mapped_column(String(100))  # "500mg", "1 viên"
    frequency: Mapped[str] = mapped_column(String(50), default="daily")  # daily, twice_daily, weekly
    times: Mapped[dict | None] = mapped_column(JSONB, default=[])  # ["08:00", "20:00"]
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ── M72: Spaced Repetition ──

class Flashcard(UserOwnedMixin, Base):
    __tablename__ = "flashcards"

    deck: Mapped[str] = mapped_column(String(100), default="general")
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    interval: Mapped[int] = mapped_column(Integer, default=1)  # days until next review
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)  # SM-2 ease
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[date] = mapped_column(Date, default=date.today)
    last_reviewed: Mapped[date | None] = mapped_column(Date)


# ── M73: Book Notes ──

class BookNote(UserOwnedMixin, Base):
    __tablename__ = "book_notes"

    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="reading")  # reading, finished, wishlist
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5
    highlights: Mapped[dict | None] = mapped_column(JSONB, default=[])  # [{text, page, note}]
    summary: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[dict | None] = mapped_column(JSONB, default=[])
