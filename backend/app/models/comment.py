import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, ModerationHideMixin, TimestampMixin, sql_in, uuid_pk
from app.models.review import MODERATION_STATUSES


class Comment(ModerationHideMixin, TimestampMixin, Base):
    """Постқа (пікір/шағым) комментарий.

    Еркін мәтін - жала-тәуекелдің өскен беті: ұзындық-шек, rate-limit
    және модератор-жасыру (аудит-логпен) қорғаныс-белдіктері міндетті.
    """

    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = uuid_pk()
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"), index=True
    )
    complaint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vacancy_complaints.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text)
    moderation_status: Mapped[str] = mapped_column(Text, server_default="published")
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "(review_id IS NULL) <> (complaint_id IS NULL)", name="exactly_one_parent"
        ),
        CheckConstraint(
            sql_in("moderation_status", MODERATION_STATUSES),
            name="moderation_status_valid",
        ),
    )
