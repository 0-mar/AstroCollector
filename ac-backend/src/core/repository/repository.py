from typing import TypeVar, Generic, Any, Optional
from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import DbEntity
from src.core.database.dependencies import DBSessionDep
from src.core.repository.exception import RepositoryException

# using session correctly
# https://docs.sqlalchemy.org/en/20/orm/session_basics.html
Entity = TypeVar("Entity", bound=DbEntity)
LIMIT = 100


# TODO: are operations correct?
class Repository(Generic[Entity]):
    def __init__(self, model: type[Entity], session: AsyncSession):
        self._session = session
        self._model = model

    async def find(self, offset: int = 0, **kwargs: dict[str, Any]) -> list[Entity]:
        stmt = select(self._model).filter_by(**kwargs).offset(offset).limit(LIMIT)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, entity_id: UUID) -> Entity:
        result = await self.get_optional(entity_id)
        if result is None:
            raise RepositoryException("Entity with ID " + str(entity_id) + " not found")
        return result

    async def get_optional(self, entity_id: UUID) -> Optional[Entity]:
        return await self._session.get(self._model, entity_id)

    async def save(self, entity: Entity) -> Entity:
        try:
            self._session.add(entity)
            await self._session.commit()
            await self._session.refresh(entity)
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryException(f"Failed to save entity: {entity}") from e

        return entity

    async def delete(self, entity_id: UUID) -> None:
        entity = await self.get(entity_id)
        await self._session.delete(entity)
        await self._session.commit()

    async def update(self, entity_id: UUID, update_data: dict[str, Any]) -> Entity:
        entity = await self.get(entity_id)

        try:
            for key, value in update_data.items():
                setattr(entity, key, value)
            await self._session.commit()
            await self._session.refresh(entity)

            return entity

        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryException(
                f"Failed to update entity with id {entity_id}"
            ) from e


def get_repository(
    entity_type: type[Entity],
) -> Callable[[DBSessionDep], Repository[Entity]]:
    def _get_repository(session: DBSessionDep) -> Repository[Entity]:
        return Repository(entity_type, session)

    return _get_repository
