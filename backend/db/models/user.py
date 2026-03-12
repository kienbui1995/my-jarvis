"""User & auth models."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    zalo_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    zalo_bot_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    telegram_id: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Ho_Chi_Minh")
    tier: Mapped[str] = mapped_column(String(20), default="free")
    preferences: Mapped[dict | None] = mapped_column(JSONB)
    goals: Mapped[dict | None] = mapped_column(JSONB)
    routines: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
