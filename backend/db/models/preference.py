"""M5 + M11 models — user preferences, prompt rules, tool permissions."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, index=True)
    tone: Mapped[str | None] = mapped_column(String(20))
    verbosity: Mapped[str | None] = mapped_column(String(20))
    language: Mapped[str | None] = mapped_column(String(10))
    interests: Mapped[list | None] = mapped_column(JSONB, default=[])
    work_context: Mapped[dict | None] = mapped_column(JSONB, default={})
    custom_rules: Mapped[dict | None] = mapped_column(JSONB, default={})
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class UserPromptRule(Base):
    __tablename__ = "user_prompt_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    rule: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    source: Mapped[str] = mapped_column(String(20), default="explicit")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_validated: Mapped[datetime | None] = mapped_column(DateTime)


class UserToolPermission(Base):
    __tablename__ = "user_tool_permissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    tool_name: Mapped[str] = mapped_column(String(100))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("user_id", "tool_name", name="uq_user_tool"),
    )
