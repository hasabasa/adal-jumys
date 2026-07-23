from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

_settings = get_settings()
_engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}
if _settings.environment == "test":
    # Тестте пул болмайды: әр тест өз event loop-ында жүреді, пулдағы
    # қосылым ескі loop-қа байланып қалады
    _engine_kwargs = {"poolclass": NullPool}

engine = create_async_engine(_settings.database_url, **_engine_kwargs)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: бір сұранысқа бір сессия."""
    async with async_session() as session:
        yield session
