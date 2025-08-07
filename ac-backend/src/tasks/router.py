from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
)
from src.data_retrieval.service import DataService
from src.tasks.schemas import (
    ConeSearchRequestDto,
    FindObjectRequestDto,
    TaskStatusDto,
    TaskIdDto,
)
from src.tasks.service import TaskService
from src.tasks.tasks import (
    catalog_cone_search,
    find_stellar_object,
    get_photometric_data,
)

DataServiceDep = Annotated[DataService, Depends(DataService)]
TaskServiceDep = Annotated[TaskService, Depends(TaskService)]

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.post("/submit-task/{plugin_id}/cone-search")
async def cone_search(
    task_service: TaskServiceDep,
    search_query_dto: ConeSearchRequestDto,
    plugin_id: UUID,
) -> TaskIdDto:
    search_query_dto.plugin_id = plugin_id
    task_id = await task_service.task(catalog_cone_search, query=search_query_dto)
    return TaskIdDto(task_id=task_id)


@router.post("/submit-task/{plugin_id}/find-object")
async def find_object(
    task_service: TaskServiceDep,
    find_object_query_dto: FindObjectRequestDto,
    plugin_id: UUID,
) -> TaskIdDto:
    find_object_query_dto.plugin_id = plugin_id
    task_id = await task_service.task(find_stellar_object, query=find_object_query_dto)
    return TaskIdDto(task_id=task_id)


@router.post("/submit-task/{plugin_id}/photometric-data")
async def submit_retrieve_data(
    task_service: TaskServiceDep,
    plugin_id: UUID,
    identificator_model: StellarObjectIdentificatorDto,
) -> TaskIdDto:
    identificator_model.plugin_id = plugin_id
    task_id = await task_service.task(
        get_photometric_data, identificator_model=identificator_model
    )
    return TaskIdDto(task_id=task_id)


@router.get("/task_status/{task_id}")
async def get_task_status(task_id: UUID, task_service: TaskServiceDep):
    """Endpoint to check the status of a task."""
    task_result = await task_service.get_task_status(task_id)
    return TaskStatusDto(task_id=task_id, status=task_result.value)
