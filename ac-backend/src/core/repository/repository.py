from typing import TypeVar, Generic, Any, Optional
from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import DbEntity
from src.core.database.dependencies import DBSessionDep
from src.core.repository.exception import RepositoryException, IntegrityException
from src.core.config.config import settings

# using session correctly
# https://docs.sqlalchemy.org/en/20/orm/session_basics.html
Entity = TypeVar("Entity", bound=DbEntity)

OPERATORS = {
    "eq": lambda col, v: col == v,
    "ne": lambda col, v: col != v,
    "gt": lambda col, v: col > v,
    "lt": lambda col, v: col < v,
    "ge": lambda col, v: col >= v,
    "le": lambda col, v: col <= v,
    "like": lambda col, v: col.like(v),
    "ilike": lambda col, v: col.ilike(v),
    "in": lambda col, v: col.in_(v),
}


class Repository(Generic[Entity]):
    def __init__(self, model: type[Entity], session: AsyncSession):
        self._session = session
        self._model = model

    def session(self):
        return self._session

    def _subexpressions_list(self, subexpressions):
        """
        Allows grouping of subexpressions inside or/and.
        :param subexpressions:
        :return:
        """
        if isinstance(subexpressions, dict):
            return self._build_filter(**subexpressions)
        if isinstance(subexpressions, list):
            subexpressions_list = []
            for subexpression in subexpressions:
                subexpressions_list.append(self._build_filter(**subexpression))
            return subexpressions_list
        else:
            raise RepositoryException(
                f"Invalid subexpression type: {type(subexpressions)}. and/or expects a dict or a list of dicts"
            )

    def _build_filter(self, **filters: dict[str, Any]):
        """
        Fields have format of <column_name>__<operator>.
        Supported operators: see supported_filters.
        :param filters:
        :return:
        """
        expressions = []

        for key, value in filters.items():
            if key == "and":
                subexpressions = self._subexpressions_list(value)
                expressions.append(and_(*subexpressions))

            if key == "or":
                subexpressions = self._subexpressions_list(value)
                expressions.append(or_(*subexpressions))

            else:
                try:
                    field, op = key.rsplit("__", 1)
                except ValueError:
                    raise RepositoryException(
                        f"Invalid filter format: {key}. Expected format: <column_name>__<operator>"
                    )

                if op not in OPERATORS:
                    raise RepositoryException(f"Unsupported filter operator: {op}")

                col = getattr(self._model, field)
                expressions.append(OPERATORS[op](col, value))

        return and_(*expressions)

    async def find(
        self,
        offset: int = 0,
        count: int = settings.MAX_PAGINATION_BATCH_COUNT,
        **filters: dict[str, Any],
    ) -> tuple[int, list[Entity]]:
        count = (
            count
            if count <= settings.MAX_PAGINATION_BATCH_COUNT
            else settings.MAX_PAGINATION_BATCH_COUNT
        )

        # build filters
        filter = self._build_filter(**filters)

        # count of all rows
        total_items_stmt = select(func.count()).select_from(self._model).filter(filter)
        total_items_result = await self._session.execute(total_items_stmt)
        total_items = total_items_result.scalar()

        # get all rows
        stmt = select(self._model).filter(filter).offset(offset).limit(count)
        result = await self._session.execute(stmt)

        return total_items, list(result.scalars().all())

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

    async def bulk_insert(self, data: list[Entity]) -> None:
        try:
            self._session.add_all(data)
            await self._session.commit()
        except IntegrityError as e:
            raise IntegrityException("Failed to insert bulk data") from e
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise RepositoryException("Failed to insert bulk data") from e


def get_repository(
    entity_type: type[Entity],
) -> Callable[[DBSessionDep], Repository[Entity]]:
    def _get_repository(session: DBSessionDep) -> Repository[Entity]:
        return Repository(entity_type, session)

    return _get_repository
