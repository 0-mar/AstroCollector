import uuid
from unittest.mock import MagicMock

import pytest

from src.core.config.config import settings
from src.tasks.model import Task
from src.tasks.router import (
    cone_search,
    find_object,
    submit_retrieve_data,
    get_task_status,
)
from src.tasks.schemas import (
    ConeSearchRequestDto,
    FindObjectRequestDto,
    TaskIdDto,
    TaskStatusDto,
)
from src.tasks.types import TaskType, TaskStatus
from src.plugin.interface.schemas import StellarObjectIdentificatorDto


# ---------------------------------------------------------------------------
# Fake repository for Task
# ---------------------------------------------------------------------------


class FakeTaskRepository:
    """Repo that behaves like Repository[Task] for the router."""

    def __init__(self):
        self.saved_tasks: list[Task] = []
        self.tasks_by_id: dict[uuid.UUID, Task] = {}

    async def save(self, task: Task) -> Task:
        # In real DB, ID is set by DB; here we simulate it
        if getattr(task, "id", None) is None:
            task.id = uuid.uuid4()
        # default status for a new task (pick something that exists)
        if getattr(task, "status", None) is None:
            task.status = TaskStatus.in_progress
        self.saved_tasks.append(task)
        self.tasks_by_id[task.id] = task
        return task

    async def get(self, task_id: uuid.UUID) -> Task:
        return self.tasks_by_id[task_id]


# ---------------------------------------------------------------------------
# /submit-task/{plugin_id}/cone-search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cone_search_submits_task_and_calls_celery(monkeypatch):
    repo = FakeTaskRepository()
    plugin_id = uuid.uuid4()

    body = ConeSearchRequestDto(
        right_ascension_deg=123.4,
        declination_deg=-22.5,
        radius_arcsec=10.0,
        plugin_id=plugin_id,
    )

    # patch the Celery task's .delay
    fake_delay = MagicMock()
    monkeypatch.setattr(
        "src.tasks.router.catalog_cone_search.delay",
        fake_delay,
    )

    response: TaskIdDto = await cone_search(
        task_repository=repo,
        search_query_dto=body,
        plugin_id=plugin_id,
    )

    # a task was created and saved
    assert len(repo.saved_tasks) == 1
    saved_task = repo.saved_tasks[0]
    assert saved_task.task_type == TaskType.object_search

    # the endpoint returned TaskIdDto with the same ID
    assert response.task_id == saved_task.id

    # Celery task was called with correct args
    fake_delay.assert_called_once()
    args, kwargs = fake_delay.call_args
    # catalog_cone_search.delay(str(task.id), search_query_dto.model_dump())
    assert args[0] == str(saved_task.id)
    payload = args[1]
    assert payload["right_ascension_deg"] == 123.4
    assert payload["declination_deg"] == -22.5
    assert payload["radius_arcsec"] == 10.0
    # plugin_id must be set by the endpoint to the URL param
    assert payload["plugin_id"] == plugin_id


# ---------------------------------------------------------------------------
# /submit-task/{plugin_id}/find-object
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_find_object_submits_task_and_calls_celery(monkeypatch):
    repo = FakeTaskRepository()
    plugin_id = uuid.uuid4()

    body = FindObjectRequestDto(
        name="Vega",
        plugin_id=plugin_id,
    )

    fake_delay = MagicMock()
    monkeypatch.setattr(
        "src.tasks.router.find_stellar_object.delay",
        fake_delay,
    )

    response: TaskIdDto = await find_object(
        task_repository=repo,
        query_dto=body,
        plugin_id=plugin_id,
    )

    assert len(repo.saved_tasks) == 1
    saved_task = repo.saved_tasks[0]
    assert saved_task.task_type == TaskType.object_search
    assert response.task_id == saved_task.id

    fake_delay.assert_called_once()
    args, kwargs = fake_delay.call_args

    assert args[0] == str(saved_task.id)
    payload = args[1]
    assert payload["name"] == "Vega"
    assert payload["plugin_id"] == plugin_id


# ---------------------------------------------------------------------------
# /submit-task/{plugin_id}/photometric-data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_retrieve_data_submits_task_and_calls_celery(
    monkeypatch,
    override_directories,
):
    repo = FakeTaskRepository()
    plugin_id = uuid.uuid4()

    identificator = StellarObjectIdentificatorDto(
        plugin_id=plugin_id,
        ra_deg=12.3,
        dec_deg=-45.6,
        name="TestStar",
        dist_arcsec=1.23,
    )

    fake_delay = MagicMock()
    monkeypatch.setattr(
        "src.tasks.router.get_photometric_data.delay",
        fake_delay,
    )

    response: TaskIdDto = await submit_retrieve_data(
        task_repository=repo,
        plugin_id=plugin_id,
        identificator_model=identificator,
    )

    assert len(repo.saved_tasks) == 1
    task = repo.saved_tasks[0]
    assert task.task_type == TaskType.photometric_data
    assert response.task_id == task.id

    fake_delay.assert_called_once()
    args, kwargs = fake_delay.call_args

    assert args[0] == str(task.id)
    payload = args[1]

    assert payload["plugin_id"] == str(plugin_id)
    assert payload["ra_deg"] == 12.3
    assert payload["dec_deg"] == -45.6
    assert payload["name"] == "TestStar"
    assert payload["dist_arcsec"] == 1.23

    csv_path_str = args[2]
    expected_filename = f"{task.id}.csv"
    assert csv_path_str.endswith(expected_filename)
    assert csv_path_str.startswith(settings.TEMP_DIR.resolve().as_posix())


# ---------------------------------------------------------------------------
# /task_status/{task_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_task_status_returns_status():
    repo = FakeTaskRepository()
    task_id = uuid.uuid4()

    task = Task(task_type=TaskType.object_search)
    task.id = task_id
    task.status = TaskStatus.completed
    await repo.save(task)

    response: TaskStatusDto = await get_task_status(
        task_id=task_id,
        task_repository=repo,
    )

    assert response.task_id == task_id
    assert response.status == TaskStatus.completed.value
