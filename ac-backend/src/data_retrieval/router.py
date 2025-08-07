from typing import Any, Annotated

from fastapi import Depends, APIRouter

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


@router.post("/object-identifiers/{task_id}")
async def retrieve_objects_identifiers(
    service: DataServiceDep, task_id: str, filters: dict[str, Any] | None = None
) -> PaginationResponseDto[StellarObjectIdentifierDto]:
    """List identifiers."""
    if filters is None:
        filters = {}
    filters["task_id"] = task_id
    identifiers = await service.list_soi(**filters)
    return identifiers


@router.post("/photometric-data/{task_id}")
async def retrieve_data(
    service: DataServiceDep, task_id: str, filters: dict[str, Any] | None = None
) -> PaginationResponseDto[PhotometricDataDto]:
    if filters is None:
        filters = {}

    filters["task_id"] = task_id
    return await service.list_photometric_data(**filters)
