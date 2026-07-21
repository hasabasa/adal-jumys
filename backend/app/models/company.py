import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, ModerationHideMixin, TimestampMixin, sql_in, uuid_pk

COMPANY_SOURCES = ("registry_import", "user_created")
REPRESENTATIVE_STATUSES = ("pending", "approved", "rejected")
PROOF_METHODS = ("domain_email", "official_letter", "other")
BADGES = (
    "salary_not_confirmed",
    "repeated_language_discrimination",
    "officially_confirmed_violation",
)


class Company(ModerationHideMixin, TimestampMixin, Base):
    """v1 - тек юрлицо (БСН). Тек ресми жалпыға ашық контактілер сақталады."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = uuid_pk()
    bin: Mapped[str] = mapped_column(String(12), unique=True)
    name: Mapped[str] = mapped_column(Text)
    legal_name: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    oked: Mapped[str | None] = mapped_column(Text)
    two_gis_url: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(sql_in("source", COMPANY_SOURCES), name="source_valid"),
        CheckConstraint("char_length(bin) = 12", name="bin_length"),
    )


class CompanyRepresentative(TimestampMixin, Base):
    """Компания-аккаунттың осы компанияны өкілдейтінін растау (right of reply алғышарты)."""

    __tablename__ = "company_representatives"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(Text, server_default="pending")
    proof_method: Mapped[str | None] = mapped_column(Text)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("company_id", "user_id"),
        CheckConstraint(sql_in("status", REPRESENTATIVE_STATUSES), name="status_valid"),
        CheckConstraint(
            f"proof_method IS NULL OR {sql_in('proof_method', PROOF_METHODS)}",
            name="proof_method_valid",
        ),
    )


class CompanyBadge(Base):
    """Паттерн-детекция нәтижесі (мыс. 5+ тәуелсіз жалақы-шағым)."""

    __tablename__ = "company_badges"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    badge: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (CheckConstraint(sql_in("badge", BADGES), name="badge_valid"),)
