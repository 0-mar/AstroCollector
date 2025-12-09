from typing import Annotated
from uuid import UUID

from fastapi import Depends, APIRouter

from src.core.config.config import settings
from src.core.exception.exceptions import APIException
from src.plugin.interface.schemas import PhotometricDataDto
from src.core.repository.repository import Filters
from src.core.service.schemas import PaginationResponseDto
from src.data_retrieval.schemas import StellarObjectIdentifierDto
from src.data_retrieval.service import DataService, PhotometricDataRepositoryDep

DataServiceDep = Annotated[DataService, Depends(DataService)]

router = APIRouter(
    prefix="/api/retrieve",
    tags=["retrieve"],
    responses={404: {"description": "Not found"}},
)


@router.post("/object-identifiers")
async def retrieve_objects_identifiers(
    service: DataServiceDep,
    filters: Filters | None = None,
    offset: int = 0,
    count: int = settings.MAX_PAGINATION_BATCH_COUNT,
) -> PaginationResponseDto[StellarObjectIdentifierDto]:
    """List identifiers from the database"""
    if filters is None or (
        "task_id__eq" not in filters.filters and "task_id__in" not in filters.filters
    ):
        raise APIException("task_id__eq or task_id__in required in filters")

    return await service.list_soi(offset, count, filters)


@router.post("/photometric-data")
async def retrieve_data(
    service: DataServiceDep,
    filters: Filters | None = None,
    offset: int = 0,
    count: int = settings.MAX_PAGINATION_BATCH_COUNT,
) -> PaginationResponseDto[PhotometricDataDto]:
    """
    Retrieve photometric data from the database.
    """
    if filters is None or (
        "task_id__eq" not in filters.filters and "task_id__in" not in filters.filters
    ):
        raise APIException("task_id__eq or task_id__in required in filters")

    return await service.list_photometric_data(
        offset=offset, count=count, filters=filters
    )


@router.get("/unique-light-filters/{task_id}")
async def retrieve_light_filters_by_task_id(
    pdr: PhotometricDataRepositoryDep, task_id: UUID
) -> list[str | None]:
    """Retrieve unique light filters for a given task ID."""
    return await pdr.distinct_entity_attribute_values(
        "light_filter", filters={"task_id__eq": str(task_id)}
    )
