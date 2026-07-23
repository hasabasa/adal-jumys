import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, sql_in, uuid_pk

REPORT_REASONS = (
    "false_facts",
    "defamation",
    "pii_exposed",
    "fake_evidence",
    "insult",
    "spam",
    "other",
)
REPORT_STATUSES = ("open", "resolved_hidden", "resolved_kept")


class PostReport(Base):
    """Постқа/комментке шағым: реактив-модерацияның кіру-арнасы.

    Екі трек: жай қолданушы (жеңіл себеп) және компания-дау
    (is_company_claim + кері дәлелдер; өкілі расталған болса verified_claim).
    """

    __tablename__ = "post_reports"

    id: Mapped[uuid.UUID] = uuid_pk()
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancy_complaints.id", ondelete="CASCADE"), index=True
    )
    comment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), index=True
    )
    reporter_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    is_company_claim: Mapped[bool] = mapped_column(server_default=text("false"))
    verified_claim: Mapped[bool] = mapped_column(server_default=text("false"))
    reason: Mapped[str] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="open")
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(review_id, complaint_id, comment_id) = 1",
            name="exactly_one_target",
        ),
        CheckConstraint(sql_in("reason", REPORT_REASONS), name="reason_valid"),
        CheckConstraint(sql_in("status", REPORT_STATUSES), name="status_valid"),
    )
