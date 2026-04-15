"""Base model with common columns — all new models should inherit from TimestampModel."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin providing id + created_at + updated_at. Use with Base."""
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class UserOwnedMixin(TimestampMixin):
    """Mixin for user-owned models: id + user_id (FK) + timestamps."""

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Dynamically add user_id FK — avoids import-time circular dependency."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "user_id") or "user_id" not in cls.__annotations__:
            from sqlalchemy import ForeignKey
            cls.user_id = mapped_column(
                UUID(as_uuid=True),
                ForeignKey("users.id", ondelete="CASCADE"),
                index=True,
            )
            cls.__annotations__["user_id"] = Mapped[uuid.UUID]
