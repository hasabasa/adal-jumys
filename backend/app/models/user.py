import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, sql_in, uuid_pk

ROLES = ("worker", "company")
TRUST_LEVELS = ("user", "trusted", "moderator", "admin")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(Text, unique=True)
    phone: Mapped[str | None] = mapped_column(Text)
    password_hash: Mapped[str] = mapped_column(Text)
    # Жария профильде ТЕК псевдоним корінеді; email/phone ешқашан ашылмайды
    pseudonym: Mapped[str] = mapped_column(Text, unique=True)
    role: Mapped[str] = mapped_column(Text)
    trust_level: Mapped[str] = mapped_column(Text, server_default="user")
    karma: Mapped[int] = mapped_column(Integer, server_default="0")
    locale: Mapped[str] = mapped_column(Text, server_default="kk")
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(sql_in("role", ROLES), name="role_valid"),
        CheckConstraint(sql_in("trust_level", TRUST_LEVELS), name="trust_level_valid"),
    )


class KarmaEvent(Base):
    """Карма өзгерісінің тарихы: users.karma - осы жазбалардың қосындысы."""

    __tablename__ = "karma_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
