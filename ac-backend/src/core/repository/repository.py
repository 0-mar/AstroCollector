from typing import TypeVar, List, Generic, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import DbEntity
from src.core.database.dependencies import DBSessionDep

# https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
Entity = TypeVar('Entity',  bound=DbEntity)
LIMIT = 100

# TODO: are operations correct?
class Repository(Generic[Entity]):

    def __init__(self, model: type[Entity], session: AsyncSession):
        self._session = session
        self._model = model

    async def find(self, offset=0, **kwargs) -> List[Entity]:
        stmt = select(self._model).filter_by(**kwargs).offset(offset).limit(LIMIT)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, entity_id: str) -> Entity:
        return await self._session.get(self._model, UUID(entity_id))

    async def save(self, entity: Entity) -> Entity:
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: str) -> None:
        entity = await self.get(entity_id)
        await self._session.delete(entity)
        await self._session.commit()

    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Entity:
        entity = await self.get(entity_id)
        for key, value in update_data.items():
            setattr(entity, key, value)
        await self._session.commit()
        await self._session.refresh(entity)

        return entity


def get_repository(entity_type: type[Entity]):
    def _get_repository(session: DBSessionDep) -> Repository[Entity]:
        return Repository(entity_type, session)
    return _get_repository