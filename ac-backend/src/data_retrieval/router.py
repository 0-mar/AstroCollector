from typing import Any, Annotated

from fastapi import Depends, APIRouter

from src.core.config.config import settings
from src.core.exception.exceptions import APIException
from src.core.integration.schemas import PhotometricDataDto
from src.core.schemas import PaginationResponseDto
from src.data_retrieval.schemas import StellarObjectIdentifierDto
from src.data_retrieval.service import DataService
from src.tasks.service import TaskService

DataServiceDep = Annotated[DataService, Depends(DataService)]
StellarObjectServiceDep = Annotated[TaskService, Depends(TaskService)]

router = APIRouter(
    prefix="/api/retrieve",
    tags=["retrieve"],
    responses={404: {"description": "Not found"}},
)


@router.post("/object-identifiers")
async def retrieve_objects_identifiers(
    service: DataServiceDep,
    filters: dict[str, Any] | None = None,
    offset: int = 0,
    count: int = settings.MAX_PAGINATION_BATCH_COUNT,
) -> PaginationResponseDto[StellarObjectIdentifierDto]:
    """List identifiers."""
    if filters is None or (
        "task_id__eq" not in filters and "task_id__in" not in filters
    ):
        raise APIException("task_id__eq or task_id__in required in filters")

    return await service.list_soi(offset, count, **filters)


@router.post("/photometric-data")
async def retrieve_data(
    service: DataServiceDep,
    filters: dict[str, Any] | None = None,
    offset: int = 0,
    count: int = settings.MAX_PAGINATION_BATCH_COUNT,
) -> PaginationResponseDto[PhotometricDataDto]:
    if filters is None or (
        "task_id__eq" not in filters and "task_id__in" not in filters
    ):
        raise APIException("task_id__eq or task_id__in required in filters")

    return await service.list_photometric_data(offset=offset, count=count, **filters)
