import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, MetaData, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# Constraint-терге болжамды атау беру: миграцияларда атаусыз constraint
# өзгертуге келмейді, сондықтан бірінші күннен конвенция бекітіледі
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


def sql_in(column: str, values: tuple[str, ...]) -> str:
    """text + CHECK энум-паттерні үшін 'col IN (...)' өрнегін құрады."""
    joined = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({joined})"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ModerationHideMixin:
    """Модератор-жасыру: физикалық өшіру жоқ, тек осы өрістер толтырылады.

    Кез келген hide/unhide әрекеті бөлек moderation_actions логына да жазылуы
    міндетті (сервис қабатында қамтамасыз етіледі).
    """

    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hidden_reason: Mapped[str | None] = mapped_column(Text)

    @declared_attr
    def hidden_by_id(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
