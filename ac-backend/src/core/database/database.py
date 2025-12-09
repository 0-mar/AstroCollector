import contextlib
import logging
from typing import Any, AsyncIterator, Optional, AsyncGenerator
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.core.config.config import settings
from src.core.database.exception import DatabaseSessionManagerException

logger = logging.getLogger(__name__)


class DbEntity(DeclarativeBase):
    """The base class for all database entities."""

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=func.gen_random_uuid()
    )


# async session:
# https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
# Heavily inspired by https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html
class AsyncDatabaseSessionManager:
    """Async database session manager. Manages the creation and closing of database sessions."""

    def __init__(self, host: str, **engine_kwargs):
        self._engine: Optional[AsyncEngine] = create_async_engine(host, **engine_kwargs)
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = (
            async_sessionmaker(
                autocommit=False, bind=self._engine, expire_on_commit=False
            )
        )

    async def close(self) -> None:
        if self._engine is None:
            raise DatabaseSessionManagerException(
                "DatabaseSessionManager is not initialized"
            )
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def transaction_connection(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise DatabaseSessionManagerException(
                "DatabaseSessionManager is not initialized"
            )

        async with self._engine.begin() as connection:
            # engine.begin() handles commit/rollback on exit
            yield connection

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise DatabaseSessionManagerException(
                "DatabaseSessionManager is not initialized"
            )

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async_sessionmanager = AsyncDatabaseSessionManager(settings.ASYNC_DATABASE_URL)


# Dependencies with yield - extra steps after finishing (session is automatically closed after the request finishes)
# https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield
async def get_async_db_session() -> AsyncGenerator[AsyncSession, Any]:
    """Function to provide a FastAPI dependency for a request-scoped AsyncSession."""
    async with async_sessionmanager.session() as session:
        yield session
