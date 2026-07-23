import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, uuid_pk


class HelpfulVote(Base):
    """Постқа (сын-пікір/шағым) "Пайдалы" дауысы: 1 юзер = 1 дауыс, toggle."""

    __tablename__ = "helpful_votes"

    id: Mapped[uuid.UUID] = uuid_pk()
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancy_complaints.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "(review_id IS NULL) <> (complaint_id IS NULL)", name="exactly_one_parent"
        ),
        # PG15+: NULLS NOT DISTINCT - бір юзер бір постқа екі дауыс бере алмайды
        UniqueConstraint(
            "user_id",
            "review_id",
            "complaint_id",
            postgresql_nulls_not_distinct=True,
        ),
    )
