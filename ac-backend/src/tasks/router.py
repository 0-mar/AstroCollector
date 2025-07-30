from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)
from src.core.schemas import PaginationResponseDto
from src.data_retrieval.schemas import StellarObjectIdentifierDto
from src.data_retrieval.service import DataService
from src.tasks.schemas import (
    ConeSearchRequestDto,
    FindObjectRequestDto,
    TaskStatusDto,
    TaskIdDto,
)
from src.tasks.service import StellarObjectService

DataServiceDep = Annotated[DataService, Depends(DataService)]
StellarObjectServiceDep = Annotated[StellarObjectService, Depends(StellarObjectService)]

router = APIRouter(
    prefix="/api/photometric-data",
    tags=["photometric-data"],
    responses={404: {"description": "Not found"}},
)


@router.post("/submit-task/{plugin_id}/cone-search")
async def cone_search(
    so_service: StellarObjectServiceDep,
    search_query_dto: ConeSearchRequestDto,
    plugin_id: UUID,
) -> TaskIdDto:
    search_query_dto.plugin_id = plugin_id
    task_id = await so_service.catalogue_cone_search(query=search_query_dto)
    return TaskIdDto(task_id=task_id)


@router.post("/submit-task/{plugin_id}/find-object")
async def find_object(
    so_service: StellarObjectServiceDep,
    find_object_query_dto: FindObjectRequestDto,
    plugin_id: UUID,
) -> TaskIdDto:
    find_object_query_dto.plugin_id = plugin_id
    task_id = await so_service.find_stellar_object(query=find_object_query_dto)
    return TaskIdDto(task_id=task_id)


@router.post("/object-identifiers")
async def retrieve_objects_identifiers(
    service: DataServiceDep, filters: dict[str, Any] | None = None
) -> PaginationResponseDto[StellarObjectIdentifierDto]:
    """List identifiers."""
    if filters is None:
        filters = {}
    identifiers = await service.list_soi(**filters)
    return identifiers


@router.post("/submit-task/{plugin_id}/retrieve")
async def submit_retrieve_data(
    so_service: StellarObjectServiceDep,
    plugin_id: UUID,
    identificator_model: StellarObjectIdentificatorDto,
) -> TaskIdDto:
    identificator_model.plugin_id = plugin_id
    task_id = await so_service.get_photometric_data(
        identificator_model=identificator_model
    )
    return TaskIdDto(task_id=task_id)


@router.post("/retrieve")
async def retrieve_data(
    service: DataServiceDep, filters: dict[str, Any] | None = None
) -> PaginationResponseDto[PhotometricDataDto]:
    return await service.list_photometric_data(**filters)


@router.get("/task_status/{task_id}")
async def get_task_status(task_id: UUID, so_service: StellarObjectServiceDep):
    """Endpoint to check the status of a task."""
    task_result = await so_service.get_task_status(task_id)
    return TaskStatusDto(task_id=task_id, status=task_result.value)
