from typing import TypeVar, Generic, Any, Optional, Literal
from collections.abc import Callable
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import DbEntity
from src.core.database.dependencies import DBSessionDep
from src.core.repository.exception import RepositoryException, IntegrityException
from src.core.config.config import settings
from src.core.repository.schemas import BaseDto

# using session correctly
# https://docs.sqlalchemy.org/en/20/orm/session_basics.html
# https://www.francoisvoron.com/blog/sqlalchemy-stop-calling-session-commit
# https://docs.sqlalchemy.org/en/20/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
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


class OrderBy(BaseDto):
    field: str
    value: Literal["asc", "desc"] = "asc"


class Distinct(BaseDto):
    fields: list[str]


class Filters(BaseDto):
    filters: dict[str, Any] = {}
    order_by: OrderBy | None = None
    distinct: Distinct | None = None


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

            elif key == "or":
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

                try:
                    col = getattr(self._model, field)
                except AttributeError as e:
                    raise RepositoryException(f"Unknown field: {e}")

                expressions.append(OPERATORS[op](col, value))

        return and_(True, *expressions)

    async def find_first(
        self,
        filters: Filters | None = None,
    ) -> Optional[Entity]:
        total_count, entities = await self.find(filters=filters)
        if total_count == 0:
            return None
        return entities[0]

    async def find_first_or_raise(
        self,
        filters: Filters | None = None,
    ) -> Optional[Entity]:
        result = await self.find_first(filters=filters)
        if result is None:
            raise RepositoryException("Entity not found")
        return result

    async def find(
        self,
        offset: int = 0,
        count: int = settings.MAX_PAGINATION_BATCH_COUNT,
        filters: Filters | None = None,
    ) -> tuple[int, list[Entity]]:
        count = (
            count
            if count <= settings.MAX_PAGINATION_BATCH_COUNT
            else settings.MAX_PAGINATION_BATCH_COUNT
        )

        # build filters
        orm_filters = self._build_filter(**(filters.filters if filters else {}))

        base_stmt = select(self._model).select_from(self._model).where(orm_filters)

        if filters is not None and filters.order_by is not None:
            try:
                order_field = getattr(self._model, filters.order_by.field)
            except AttributeError as e:
                raise RepositoryException(f"Unknown field: {e}")

            base_stmt = base_stmt.order_by(
                desc(order_field)
                if filters.order_by.value == "desc"
                else asc(order_field)
            )

        if filters is not None and filters.distinct is not None:
            try:
                cols = [getattr(self._model, name) for name in filters.distinct.fields]
            except AttributeError as e:
                raise RepositoryException(f"Unknown distinct field: {e}")
            base_stmt = base_stmt.distinct(*cols)

        # count of all rows
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        entity_count_result = await self._session.execute(count_stmt)
        entity_count = entity_count_result.scalar()

        # get all rows
        entity_stmt = base_stmt.offset(offset).limit(count)
        result = await self._session.execute(entity_stmt)

        return entity_count, list(result.scalars().all())

    async def distinct_entity_attribute_values(
        self,
        attribute: str,
        filters: dict[str, Any] | None = None,
    ) -> list[Any]:
        if filters is None:
            filters = {}

        # build filters
        orm_filters = self._build_filter(**filters)

        try:
            distinct_field = getattr(self._model, attribute)
        except AttributeError as e:
            raise RepositoryException(f"Unknown field: {e}")

        distinct_stmt = (
            select(distinct_field)
            .select_from(self._model)
            .where(orm_filters)
            .distinct(distinct_field)
        )

        result = await self._session.execute(distinct_stmt)
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
