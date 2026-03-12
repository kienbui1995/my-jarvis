"""Evidence log model for M9 audit trail."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base


class EvidenceLog(Base):
    __tablename__ = "evidence_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    session_id: Mapped[str] = mapped_column(String(100), default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    node: Mapped[str] = mapped_column(String(50))
    event_type: Mapped[str] = mapped_column(String(50))
    tool_name: Mapped[str] = mapped_column(String(100), default="")
    tool_input: Mapped[dict | None] = mapped_column(JSONB)
    tool_output: Mapped[str] = mapped_column(Text, default="")
    model_used: Mapped[str] = mapped_column(String(50), default="")
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
