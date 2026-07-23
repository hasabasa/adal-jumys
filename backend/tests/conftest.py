import asyncio
import os

# МАҢЫЗДЫ: app импортталмай тұрып орнатылуы керек (Settings оқып қояды).
# CI-да DATABASE_URL сырттан беріледі, setdefault оны басып тастамайды.
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://hasen@localhost:5432/adal_jumys_test"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum-for-hs256")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

import app.models  # noqa: F401
from app.db.base import Base
from app.db.session import async_session, engine
from app.main import app as fastapi_app
from app.models import User
from app.services.bin_check import is_valid_bin

PASSWORD = "sekret123"


@pytest.fixture(scope="session", autouse=True)
def create_schema():
    async def _create():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_create())


@pytest.fixture(autouse=True)
def clean_db(create_schema):
    yield
    async def _clean():
        tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
        async with engine.begin() as conn:
            await conn.execute(text(f"TRUNCATE {tables} CASCADE"))
        await engine.dispose()

    asyncio.run(_clean())


@pytest.fixture
def client():
    with TestClient(fastapi_app) as c:
        yield c


@pytest.fixture
def register(client):
    def _register(email: str, pseudonym: str, role: str = "worker") -> dict:
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": PASSWORD,
                "pseudonym": pseudonym,
                "role": role,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _register


@pytest.fixture
def auth_header(client):
    def _auth_header(email: str) -> dict:
        response = client.post(
            "/auth/login", data={"username": email, "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _auth_header


@pytest.fixture
def promote():
    """Юзердің trust_level-ін тікелей БД арқылы көтеру (тест-жол)."""

    def _promote(email: str, level: str = "moderator") -> None:
        async def _run():
            async with async_session() as db:
                user = await db.scalar(select(User).where(User.email == email))
                user.trust_level = level
                await db.commit()

        asyncio.run(_run())

    return _promote


def make_bin(prefix: str) -> str:
    """11 цифрлы префикстен чексумы жарамды БСН құрады."""
    assert len(prefix) == 11 and prefix.isdigit()
    for d in range(10):
        candidate = f"{prefix}{d}"
        if is_valid_bin(candidate):
            return candidate
    raise AssertionError(f"Жарамды чексум табылмады: {prefix}")


REVIEW_BODY = (
    "Zhalaqy 3 ai keshikti, pensionka audarylmady, dalel skrini tirkeldi. "
    "Faktimen zhazylgan otzyv."
)
