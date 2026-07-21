import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, ModerationHideMixin, TimestampMixin, sql_in, uuid_pk
from app.models.review import MODERATION_STATUSES

COMPLAINT_CATEGORIES = (
    "salary_fraud",
    "fake_vacancy",
    "paid_training",
    "unethical_questions",
    "rudeness",
    "ghost_vacancy",
    "unpaid_test_task",
    "discrimination",
)
COMPLAINT_STAGES = ("announcement", "call", "interview", "offer")
SOURCE_TYPES = ("hh", "olx", "instagram", "threads", "telegram", "whatsapp", "other")

DISCRIMINATION_KINDS = ("language", "age", "gender", "ethnicity", "other")
DISCRIMINATION_FORMS = ("vacancy_text", "interview", "at_work")


class VacancyComplaint(ModerationHideMixin, TimestampMixin, Base):
    """Вакансия-шағым (2-ось: жалдаушы осі - статистика + бейджтер, сан емес)."""

    __tablename__ = "vacancy_complaints"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    # salary_fraud: айырманы жүйе өзі есептеп көрсетеді
    advertised_salary: Mapped[int | None] = mapped_column(Integer)
    actual_salary: Mapped[int | None] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    moderation_status: Mapped[str] = mapped_column(Text, server_default="pending")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(sql_in("category", COMPLAINT_CATEGORIES), name="category_valid"),
        CheckConstraint(sql_in("stage", COMPLAINT_STAGES), name="stage_valid"),
        CheckConstraint(sql_in("source_type", SOURCE_TYPES), name="source_type_valid"),
        CheckConstraint(
            sql_in("moderation_status", MODERATION_STATUSES),
            name="moderation_status_valid",
        ),
        CheckConstraint(
            "advertised_salary IS NULL OR advertised_salary >= 0",
            name="advertised_salary_positive",
        ),
        CheckConstraint(
            "actual_salary IS NULL OR actual_salary >= 0",
            name="actual_salary_positive",
        ),
    )


class DiscriminationDetail(TimestampMixin, Base):
    """Кемсітушілік блогы: отзывқа НЕМЕСЕ шағымға тіркеледі (дәл біреуіне)."""

    __tablename__ = "discrimination_details"

    id: Mapped[uuid.UUID] = uuid_pk()
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancy_complaints.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(Text)
    form: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "(review_id IS NULL) <> (complaint_id IS NULL)", name="exactly_one_parent"
        ),
        CheckConstraint(sql_in("kind", DISCRIMINATION_KINDS), name="kind_valid"),
        CheckConstraint(sql_in("form", DISCRIMINATION_FORMS), name="form_valid"),
    )
