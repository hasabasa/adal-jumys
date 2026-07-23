import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, sql_in, uuid_pk

MODERATION_ACTIONS = (
    "hide",
    "unhide",
    "approve",
    "reject",
    "mask_pii",
    "verify_review",
    "award_badge",
    "revoke_badge",
    "ban_user",
    "other",
)
TARGET_TYPES = (
    "review",
    "complaint",
    "evidence",
    "response",
    "company",
    "user",
    "badge",
    "representative",
)
APPEAL_STATUSES = ("open", "upheld", "overturned")


class ModerationAction(Base):
    """Ашық аудит-лог: append-only, UPDATE/DELETE жоқ (сервис қабатында да,
    кейін БД-триггермен де қорғалады). reason - жария көрінетін мәтін.

    Екі адам ережесі: маңызды әрекетке second_approver_id толтырылады.
    Мүдде қақтығысы автоблогы сервис қабатында тексеріледі.
    """

    __tablename__ = "moderation_actions"

    id: Mapped[uuid.UUID] = uuid_pk()
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(Text)
    target_type: Mapped[str] = mapped_column(Text)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    reason: Mapped[str] = mapped_column(Text)
    second_approver_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(sql_in("action", MODERATION_ACTIONS), name="action_valid"),
        CheckConstraint(sql_in("target_type", TARGET_TYPES), name="target_type_valid"),
    )


class Appeal(Base):
    """Модераторлық шешімге апелляция; overturn-метрика осыдан есептеледі."""

    __tablename__ = "appeals"

    id: Mapped[uuid.UUID] = uuid_pk()
    action_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("moderation_actions.id", ondelete="CASCADE"), index=True
    )
    appellant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="open")
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(sql_in("status", APPEAL_STATUSES), name="status_valid"),
    )
