"""V9 models — Finance & Life management."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import Base, UserOwnedMixin


# ── M53: Bill Reminders ──

class BillReminder(UserOwnedMixin, Base):
    __tablename__ = "bill_reminders"

    name: Mapped[str] = mapped_column(String(255))  # "Tiền điện", "Internet"
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="VND")
    due_day: Mapped[int] = mapped_column(Integer)  # Day of month (1-31)
    frequency: Mapped[str] = mapped_column(String(20), default="monthly")  # monthly, quarterly, yearly
    category: Mapped[str] = mapped_column(String(50), default="utilities")
    auto_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    last_paid: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


# ── M54: Subscription Tracker ──

class Subscription(UserOwnedMixin, Base):
    __tablename__ = "subscriptions"

    name: Mapped[str] = mapped_column(String(255))  # "Netflix", "Spotify"
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="VND")
    frequency: Mapped[str] = mapped_column(String(20), default="monthly")
    category: Mapped[str] = mapped_column(String(50), default="entertainment")
    next_billing: Mapped[date | None] = mapped_column(Date)
    cancel_url: Mapped[str | None] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ── M55+M56: Contact CRM + Birthday ──

class Contact(UserOwnedMixin, Base):
    __tablename__ = "contacts"

    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    relationship: Mapped[str | None] = mapped_column(String(50))  # family, friend, colleague, client
    birthday: Mapped[date | None] = mapped_column(Date)
    anniversary: Mapped[date | None] = mapped_column(Date)
    company: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    preferences: Mapped[dict | None] = mapped_column(JSONB, default={})  # likes, dislikes, gift ideas
    last_contact: Mapped[date | None] = mapped_column(Date)


# ── M57: Document Vault ──

class Document(UserOwnedMixin, Base):
    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(255))  # "CCCD", "Passport"
    doc_type: Mapped[str] = mapped_column(String(50))  # id_card, passport, insurance, contract, certificate
    file_key: Mapped[str | None] = mapped_column(String(500))  # MinIO key
    doc_number: Mapped[str | None] = mapped_column(String(100))
    issuer: Mapped[str | None] = mapped_column(String(255))
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, default={})


# ── M59: Shopping Lists ──

class ShoppingList(UserOwnedMixin, Base):
    __tablename__ = "shopping_lists"

    name: Mapped[str] = mapped_column(String(255), default="Danh sách mua sắm")
    completed: Mapped[bool] = mapped_column(Boolean, default=False)


class ShoppingItem(Base):
    __tablename__ = "shopping_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shopping_lists.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit: Mapped[str | None] = mapped_column(String(20))
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
