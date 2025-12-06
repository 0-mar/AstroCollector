import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from src.core.config.config import settings
from src.main import app


@pytest.fixture
def override_directories(monkeypatch):
    """
    Runs once before all tests and once after all tests.
    """
    # ---------- setup (before all tests) ----------
    base_dir = Path("..")

    plugins_dir = base_dir / "plugins"
    resources_dir = base_dir / "resources"
    temp_dir = base_dir / "temp"
    logs_dir = base_dir / "logs"

    if not plugins_dir.exists():
        plugins_dir.mkdir()
    if not resources_dir.exists():
        resources_dir.mkdir()
    if not temp_dir.exists():
        temp_dir.mkdir()
    if not logs_dir.exists():
        logs_dir.mkdir()

    monkeypatch.setattr(type(settings), "ROOT_DIR", base_dir, raising=True)

    yield  # run all tests

    # teardown (after all tests) ----------
    shutil.rmtree(plugins_dir)
    shutil.rmtree(resources_dir)
    shutil.rmtree(temp_dir)
    shutil.rmtree(logs_dir)


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """One async engine for all tests."""
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL, pool_size=10, echo=True, max_overflow=10
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session_maker(async_engine):
    TestingAsyncSessionLocal = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    yield TestingAsyncSessionLocal


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine, async_session_maker):
    """The expectation with async_sessions is that the
    transactions be called on the connection object instead of the
    session object.
    Detailed explanation of async transactional tests
    <https://github.com/sqlalchemy/sqlalchemy/issues/5811>
    """

    connection = await async_engine.connect()
    trans = await connection.begin()
    async_session = async_session_maker(bind=connection)
    nested = await connection.begin_nested()

    @event.listens_for(async_session.sync_session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested

        if not nested.is_active:
            nested = connection.sync_connection.begin_nested()

    yield async_session

    await trans.rollback()
    await async_session.close()
    await connection.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient fixture
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000/api/"
    ) as ac:
        yield ac
