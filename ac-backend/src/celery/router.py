from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
)
from src.core.repository.repository import Repository, get_repository
from src.tasks.model import Task
from src.tasks.schemas import (
    ConeSearchRequestDto,
    FindObjectRequestDto,
    TaskStatusDto,
    TaskIdDto,
)
import src.core.celery.worker as celery_worker

TaskRepositoryDep = Annotated[
    Repository[Task],
    Depends(get_repository(Task)),
]


router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


async def create_task(task_repository: Repository[Task]):
    task = await task_repository.save(Task())
    return task.id


@router.post("/submit-task/{plugin_id}/cone-search")
async def cone_search(
    task_repository: TaskRepositoryDep,
    search_query_dto: ConeSearchRequestDto,
    plugin_id: UUID,
) -> TaskIdDto:
    search_query_dto.plugin_id = plugin_id
    task_id = await create_task(task_repository)

    celery_worker.catalog_cone_search.delay(str(task_id), search_query_dto.model_dump())

    return TaskIdDto(task_id=task_id)


@router.post("/submit-task/{plugin_id}/find-object")
async def find_object(
    task_repository: TaskRepositoryDep,
    query_dto: FindObjectRequestDto,
    plugin_id: UUID,
) -> TaskIdDto:
    query_dto.plugin_id = plugin_id
    task_id = await create_task(task_repository)

    celery_worker.find_stellar_object.delay(str(task_id), query_dto.model_dump())

    return TaskIdDto(task_id=task_id)


@router.post("/submit-task/{plugin_id}/photometric-data")
async def submit_retrieve_data(
    task_repository: TaskRepositoryDep,
    plugin_id: UUID,
    identificator_model: StellarObjectIdentificatorDto,
) -> TaskIdDto:
    identificator_model.plugin_id = plugin_id
    task_id = await create_task(task_repository)

    celery_worker.get_photometric_data.delay(
        str(task_id), identificator_model.model_dump()
    )

    return TaskIdDto(task_id=task_id)


@router.get("/task_status/{task_id}")
async def get_task_status(task_id: UUID, task_repository: TaskRepositoryDep):
    """Endpoint to check the status of a task."""
    task = await task_repository.get(task_id)
    return TaskStatusDto(task_id=task_id, status=task.status.value)
