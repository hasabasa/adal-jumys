import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, ModerationHideMixin, TimestampMixin, sql_in, uuid_pk

VERIFICATION_STATUSES = ("unverified", "pending", "verified", "rejected")
MODERATION_STATUSES = ("pending", "published", "hidden")
VERIFICATION_METHODS = ("employment_contract", "bank_statement", "other")
VERIFICATION_DECISIONS = ("approved", "rejected")


class Review(ModerationHideMixin, TimestampMixin, Base):
    """Жұмысшы отзывы (1-ось: жұмыс беруші рейтингі, Байес орташасы)."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    overall_score: Mapped[int] = mapped_column(SmallInteger)
    score_salary_timeliness: Mapped[int | None] = mapped_column(SmallInteger)
    score_pension: Mapped[int | None] = mapped_column(SmallInteger)
    score_overtime: Mapped[int | None] = mapped_column(SmallInteger)
    score_contract: Mapped[int | None] = mapped_column(SmallInteger)
    body: Mapped[str] = mapped_column(Text)
    # ҚР ЕК бойынша жұмыс беруші қызметкерге айыппұл сала алмайды - бұл өріс
    # сол заңсыз тәжірибені құрылымды түрде тіркейді (бейдж-детекцияға негіз)
    illegal_fines: Mapped[bool] = mapped_column(server_default=text("false"))
    employment_start: Mapped[date | None] = mapped_column(Date)
    employment_end: Mapped[date | None] = mapped_column(Date)
    verification_status: Mapped[str] = mapped_column(Text, server_default="unverified")
    moderation_status: Mapped[str] = mapped_column(Text, server_default="pending")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        # 1 компанияға 1 юзерден 1 отзыв (абьюз-қорғаныс)
        UniqueConstraint("company_id", "author_id"),
        CheckConstraint("overall_score BETWEEN 1 AND 10", name="overall_score_range"),
        CheckConstraint(
            "score_salary_timeliness IS NULL OR score_salary_timeliness BETWEEN 1 AND 10",
            name="score_salary_range",
        ),
        CheckConstraint(
            "score_pension IS NULL OR score_pension BETWEEN 1 AND 10",
            name="score_pension_range",
        ),
        CheckConstraint(
            "score_overtime IS NULL OR score_overtime BETWEEN 1 AND 10",
            name="score_overtime_range",
        ),
        CheckConstraint(
            "score_contract IS NULL OR score_contract BETWEEN 1 AND 10",
            name="score_contract_range",
        ),
        CheckConstraint(
            sql_in("verification_status", VERIFICATION_STATUSES),
            name="verification_status_valid",
        ),
        CheckConstraint(
            sql_in("moderation_status", MODERATION_STATUSES),
            name="moderation_status_valid",
        ),
    )


class VerificationRecord(Base):
    """Верификация фактісі. Дәлел-файл модератор шешімінен кейін БІРДЕН өшіріледі,
    осы жазба ғана қалады (дербес деректі минимизациялау)."""

    __tablename__ = "verification_records"

    id: Mapped[uuid.UUID] = uuid_pk()
    review_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), unique=True
    )
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    method: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(sql_in("method", VERIFICATION_METHODS), name="method_valid"),
        CheckConstraint(
            sql_in("decision", VERIFICATION_DECISIONS), name="decision_valid"
        ),
    )
