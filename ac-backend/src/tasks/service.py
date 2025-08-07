import logging
from typing import Annotated
from uuid import UUID

from fastapi import BackgroundTasks, Depends

from src.core.repository.repository import Repository, get_repository
from src.tasks.model import Task
from src.tasks.types import TaskStatus


TaskRepositoryDep = Annotated[
    Repository[Task],
    Depends(get_repository(Task)),
]

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepositoryDep,
        background_tasks: BackgroundTasks,
    ) -> None:
        self._task_repository = task_repository
        self._background_tasks = background_tasks

    async def task(self, f, *args, **kwargs):
        logger.info("Starting task")
        task: Task = await self._task_repository.save(Task())
        logger.info(
            f"Task {task.id} created. Starting task in background: {f.__name__}"
        )

        self._background_tasks.add_task(f, task.id, *args, **kwargs)

        return task.id

    async def get_task_status(self, task_id: UUID) -> TaskStatus:
        task = await self._task_repository.get(task_id)
        return task.status
