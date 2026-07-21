import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, sql_in, uuid_pk

TIP_STATUSES = ("draft", "approved")


class DailyTip(TimestampMixin, Base):
    """v1.x «Бүгінгі кеңес»: ЕК бабына байланған сауаттылық мини-кеңес.

    Алдын ала батчпен генерацияланып, адам-ревьюден кейін approved болады;
    фронт күн сайын published_on бойынша ротациялайды. Live LLM жоқ.
    """

    __tablename__ = "daily_tips"

    id: Mapped[uuid.UUID] = uuid_pk()
    labor_code_article: Mapped[str | None] = mapped_column(Text)
    body_kk: Mapped[str] = mapped_column(Text)
    body_ru: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default="draft")
    published_on: Mapped[date | None] = mapped_column(Date, index=True)

    __table_args__ = (
        CheckConstraint(sql_in("status", TIP_STATUSES), name="status_valid"),
    )
