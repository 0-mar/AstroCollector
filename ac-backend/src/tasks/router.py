from typing import Annotated, Any
from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter, Depends

from src.core.celery import celery_worker
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
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    TaskIdDto,
)

DataServiceDep = Annotated[DataService, Depends(DataService)]

router = APIRouter(
    prefix="/api/photometric-data",
    tags=["photometric-data"],
    responses={404: {"description": "Not found"}},
)


@router.post("/submit-task/{plugin_id}/cone-search")
async def cone_search(
    search_query_dto: ConeSearchRequestDto,
    plugin_id: UUID,
) -> TaskIdDto:
    search_query_dto.plugin_id = plugin_id
    task = celery_worker.cone_search.delay(search_query_dto)
    return TaskIdDto(task_id=task.id)


@router.post("/submit-task/{plugin_id}/find-object")
async def find_object(
    find_object_query_dto: FindObjectRequestDto,
    plugin_id: UUID,
) -> TaskIdDto:
    find_object_query_dto.plugin_id = plugin_id
    task = celery_worker.find_object.delay(find_object_query_dto.model_dump())
    return TaskIdDto(task_id=task.id)


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
    plugin_id: UUID,
    identificator_model: StellarObjectIdentificatorDto,
) -> TaskIdDto:
    identificator_model.plugin_id = plugin_id
    task = celery_worker.get_photometric_data.delay(identificator_model)
    return TaskIdDto(task_id=task.id)


@router.post("/retrieve")
async def retrieve_data(
    service: DataServiceDep, filters: dict[str, Any] | None = None
) -> PaginationResponseDto[PhotometricDataDto]:
    return await service.list_photometric_data(**filters)


@router.get("/task_status/{task_id}")
async def get_task_status(task_id: UUID):
    """Endpoint to check the status of a task."""
    task_result = AsyncResult(str(task_id))
    task_status_dto = TaskStatusDto(task_id=task_id, status="")
    if task_result.ready():  # If the task is done
        task_status_dto.status = STATUS_COMPLETED
    elif task_result.failed():  # If the task failed
        task_status_dto.status = STATUS_FAILED
    else:  # If the task is still in progress
        task_status_dto.status = STATUS_IN_PROGRESS

    return task_status_dto
