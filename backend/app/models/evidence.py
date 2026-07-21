import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, sql_in, uuid_pk
from app.models.review import MODERATION_STATUSES

EVIDENCE_PURPOSES = ("public_evidence", "verification")
EVIDENCE_STATUSES = ("pending_moderation", "visible", "hidden", "deleted")


class EvidenceFile(TimestampMixin, Base):
    """Дәлел-файл метадеректері. Файлдың өзі S3-те, БД-да ЕМЕС.

    purpose='verification' файлы модератор шешімінен кейін S3-тен өшіріліп,
    мұнда status='deleted' болады (verification_records жазбасы қалады).
    Жария дәлел модерациядан өткенше көрсетілмейді; PII маскіленеді.
    """

    __tablename__ = "evidence_files"

    id: Mapped[uuid.UUID] = uuid_pk()
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancy_complaints.id", ondelete="CASCADE"), index=True
    )
    purpose: Mapped[str] = mapped_column(Text, server_default="public_evidence")
    s3_key: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    pii_masked: Mapped[bool] = mapped_column(server_default=text("false"))
    status: Mapped[str] = mapped_column(Text, server_default="pending_moderation")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "(review_id IS NULL) <> (complaint_id IS NULL)", name="exactly_one_parent"
        ),
        CheckConstraint(sql_in("purpose", EVIDENCE_PURPOSES), name="purpose_valid"),
        CheckConstraint(sql_in("status", EVIDENCE_STATUSES), name="status_valid"),
    )


class CompanyResponse(TimestampMixin, Base):
    """Right of reply: компанияның отзыв/шағымға ресми жауабы."""

    __tablename__ = "company_responses"

    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    # Жауапты жазған өкіл (company_representatives арқылы расталған юзер)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancy_complaints.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    moderation_status: Mapped[str] = mapped_column(Text, server_default="pending")

    __table_args__ = (
        CheckConstraint(
            "(review_id IS NULL) <> (complaint_id IS NULL)", name="exactly_one_parent"
        ),
        CheckConstraint(
            sql_in("moderation_status", MODERATION_STATUSES),
            name="moderation_status_valid",
        ),
    )
