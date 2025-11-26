from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncTransaction,
    AsyncSession,
    create_async_engine,
)

from src.core.config.config import settings
from src.main import app


# TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
#
# test_engine = create_async_engine(
#     TEST_DATABASE_URL,
#     echo=False,
#     future=True,
#     connect_args={"check_same_thread": False},  # needed for SQLite
# )
#
# AsyncTestingSessionLocal = async_sessionmaker(
#     bind=test_engine,
#     expire_on_commit=False,
# )
#
# # ---------------------------------------------------------------------------
# # Override the FastAPI dependency: get_async_db_session
# # ---------------------------------------------------------------------------
# async def override_get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
#     async with AsyncTestingSessionLocal() as session:
#         yield session
#
#
# app.dependency_overrides[get_async_db_session] = override_get_async_db_session
#
# @pytest.fixture(scope="session", autouse=True)
# def prepare_database() -> None:
#     """
#     Create all tables before running tests, and drop them afterwards.
#     Uses DbEntity.metadata, which should include all models inheriting DbEntity.
#     """
#
#     async def init_models() -> None:
#         async with test_engine.begin() as conn:
#             await conn.run_sync(DbEntity.metadata.create_all)
#
#     async def drop_models() -> None:
#         async with test_engine.begin() as conn:
#             await conn.run_sync(DbEntity.metadata.drop_all)
#
#     asyncio.run(init_models())
#     yield
#     asyncio.run(drop_models())
#
#     # remove SQLite file
#     if os.path.exists("test.db"):
#         os.remove("test.db")

# pytest + sqlalchemy async tests
# https://gist.github.com/e-kondr01/969ae24f2e2f31bd52a81fa5a1fe0f96
# https://www.core27.co/post/transactional-unit-tests-with-pytest-and-async-sqlalchemy

engine = create_async_engine(settings.ASYNC_DATABASE_URL)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def connection(anyio_backend) -> AsyncGenerator[AsyncConnection, None]:
    async with engine.connect() as connection:
        yield connection


@pytest.fixture()
async def transaction(
    connection: AsyncConnection,
) -> AsyncGenerator[AsyncTransaction, None]:
    async with connection.begin() as transaction:
        yield transaction


# Use this fixture to get SQLAlchemy's AsyncSession.
# All changes that occur in a test function are rolled back
# after function exits, even if session.commit() is called
# in inner functions
@pytest.fixture()
async def db_session(
    connection: AsyncConnection, transaction: AsyncTransaction
) -> AsyncGenerator[AsyncSession, None]:
    async_session = AsyncSession(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )

    yield async_session

    await transaction.rollback()


# # ---------------------------------------------------------------------------
# # Override the FastAPI dependency: get_async_db_session
# # ---------------------------------------------------------------------------
# async def override_get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
#     async with AsyncTestingSessionLocal() as session:
#         yield session
#
#
# app.dependency_overrides[get_async_db_session] = override_get_async_db_session


# ---------------------------------------------------------------------------
# FastAPI TestClient fixture
# ---------------------------------------------------------------------------
@pytest.fixture()
def client() -> TestClient:
    """
    Synchronous TestClient that internally runs the async app.
    """
    return TestClient(app)
