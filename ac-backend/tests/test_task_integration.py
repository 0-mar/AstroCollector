import uuid

import pytest
import pytest_asyncio
from astropy import units as u
from astropy.coordinates import SkyCoord
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
)

from src.core.celery.worker import celery_app
from src.core.database.database import get_async_db_session
from src.main import app
from src.plugin.interface.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)
from src.tasks.model import Task, StellarObjectIdentifier, PhotometricData
from src.tasks.types import TaskType, TaskStatus
from src.tasks import tasks as tasks_module


@pytest.fixture(autouse=True)
def configure_celery_for_tests():
    """
    Configure Celery to run tasks eagerly and use an in-memory broker/backend
    so tests don't need a real Redis.
    """
    old_broker_url = celery_app.conf.broker_url
    old_result_backend = celery_app.conf.result_backend
    old_always_eager = celery_app.conf.task_always_eager
    old_eager_propagates = celery_app.conf.task_eager_propagates

    celery_app.conf.broker_url = "memory://"
    celery_app.conf.result_backend = "cache+memory://"
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True

    try:
        yield
    finally:
        celery_app.conf.broker_url = old_broker_url
        celery_app.conf.result_backend = old_result_backend
        celery_app.conf.task_always_eager = old_always_eager
        celery_app.conf.task_eager_propagates = old_eager_propagates


# ------------------------------
# FastAPI AsyncClient fixture
# ------------------------------
@pytest_asyncio.fixture
async def fastapi_app(async_engine):
    # uncomment if lifespan function is needed
    # @asynccontextmanager
    # async def lifespan(app):
    #     sync_http_client = Client()
    #     async with AsyncClient() as http_client:
    #         yield {"async_http_client": http_client, "sync_http_client": Client()}
    #         # The AsyncClient closes on shutdown
    #
    #     sync_http_client.close()

    # async with LifespanManager(app) as manager:
    #      yield manager.app

    # Build sessionmaker bound to this engine
    TestingSessionLocal = async_sessionmaker(
        async_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async def override_get_db_session():
        async with TestingSessionLocal() as session:
            yield session

    # override the low-level DB dependency
    app.dependency_overrides[get_async_db_session] = override_get_db_session
    yield app


@pytest_asyncio.fixture
async def client(fastapi_app: FastAPI):
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://localhost/api") as ac:
        yield ac


# --------------------
# Integration tests
# ---------------------
@pytest.mark.asyncio
async def test_cone_search_with_celery(
    client,
    db_session,
    override_directories,
    monkeypatch,
):
    plugin_id = uuid.uuid4()

    class FakePlugin:
        def list_objects(self, coords, radius_arcsec, plugin_id_arg, resources_dir):
            dto1 = StellarObjectIdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=10.0,
                dec_deg=-20.0,
                name="Star A",
                dist_arcsec=1.0,
            )
            dto2 = StellarObjectIdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=11.0,
                dec_deg=-21.0,
                name="Star B",
                dist_arcsec=2.0,
            )
            yield [dto1, dto2]

    def fake_get_plugin_instance(self, plugin_id_param):
        assert plugin_id_param == plugin_id
        return FakePlugin()

    monkeypatch.setattr(
        tasks_module.SyncTaskService,
        "get_plugin_instance",
        fake_get_plugin_instance,
        raising=True,
    )

    body = {
        "right_ascension_deg": 123.4,
        "declination_deg": -22.5,
        "radius_arcsec": 10.0,
        "plugin_id": str(plugin_id),
    }

    # call the real HTTP endpoint - this creates the Task via async repo
    # and triggers catalog_cone_search.delay(), which Celery runs eagerly
    resp = await client.post(
        f"/tasks/submit-task/{plugin_id}/cone-search",
        json=body,
    )

    assert resp.status_code == 200
    data = resp.json()
    task_id = uuid.UUID(data["task_id"])

    # check that the Task exists and status was set to COMPLETED by the Celery task
    result = await db_session.execute(select(Task).where(Task.id == task_id))
    task_obj = result.scalar_one()
    assert task_obj.task_type == TaskType.object_search
    assert task_obj.status == TaskStatus.completed

    # check that SyncTaskService.bulk_insert inserted the StellarObjectIdentifier rows
    result = await db_session.execute(
        select(StellarObjectIdentifier).where(
            StellarObjectIdentifier.task_id == task_id
        )
    )
    identifiers = result.scalars().all()
    assert len(identifiers) == 2

    identifiers_by_name = {id.identifier["name"] for id in identifiers}
    assert identifiers_by_name == {"Star A", "Star B"}


@pytest.mark.asyncio
async def test_find_object_with_celery(
    client,
    db_session,
    override_directories,
    monkeypatch,
):
    """
    Full integration for /submit-task/{plugin_id}/find-object:

    HTTP -> router -> Celery (eager) -> find_stellar_object task
         -> resolve_name_to_coordinates (patched)
         -> cone_search -> SyncTaskService (real bulk_insert + set_task_status)
         -> DB
    """
    plugin_id = uuid.uuid4()

    def fake_resolve_name_to_coordinates(name: str, http_client):
        assert name == "Vega"
        return SkyCoord(ra=279.23473479 * u.deg, dec=38.78368896 * u.deg, frame="icrs")

    monkeypatch.setattr(
        tasks_module,
        "resolve_name_to_coordinates",
        fake_resolve_name_to_coordinates,
        raising=True,
    )

    class FakePlugin:
        def list_objects(self, coords, radius_arcsec, plugin_id_arg, resources_dir):
            dto1 = StellarObjectIdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=10.0,
                dec_deg=-20.0,
                name="Star A",
                dist_arcsec=1.0,
            )
            dto2 = StellarObjectIdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=11.0,
                dec_deg=-21.0,
                name="Star B",
                dist_arcsec=2.0,
            )
            yield [dto1, dto2]

    def fake_get_plugin_instance(self, plugin_id_param):
        assert plugin_id_param == plugin_id
        return FakePlugin()

    monkeypatch.setattr(
        tasks_module.SyncTaskService,
        "get_plugin_instance",
        fake_get_plugin_instance,
        raising=True,
    )

    body = {
        "name": "Vega",
        "plugin_id": str(plugin_id),
    }

    resp = await client.post(
        f"/tasks/submit-task/{plugin_id}/find-object",
        json=body,
    )

    assert resp.status_code == 200
    data = resp.json()
    task_id = uuid.UUID(data["task_id"])

    # check Task in DB - created with correct type and status COMPLETED
    result = await db_session.execute(select(Task).where(Task.id == task_id))
    task_obj = result.scalar_one()
    assert task_obj.task_type == TaskType.object_search
    assert task_obj.status == TaskStatus.completed

    # check that identifiers were inserted by SyncTaskService
    result = await db_session.execute(
        select(StellarObjectIdentifier).where(
            StellarObjectIdentifier.task_id == task_id
        )
    )
    identifiers = result.scalars().all()
    assert len(identifiers) == 2

    names = {id.identifier["name"] for id in identifiers}
    assert names == {"Star A", "Star B"}


@pytest.mark.asyncio
async def test_photometric_data_with_celery(
    client,
    db_session,
    override_directories,
    monkeypatch,
):
    """
    Full integration for /submit-task/{plugin_id}/photometric-data:

    HTTP -> router -> Celery (eager) -> get_photometric_data task
         -> SyncTaskService.get_plugin_instance (patched)
         -> plugin.get_photometric_data (fake)
         -> SyncTaskService.bulk_insert -> DB
         -> set_task_status(COMPLETED)
    """
    plugin_id = uuid.uuid4()

    class FakePlugin:
        def get_photometric_data(self, identificator, csv_path, resources_dir):
            assert identificator.plugin_id == plugin_id
            assert identificator.name == "TestStar"

            dto1 = PhotometricDataDto(
                plugin_id=plugin_id,
                julian_date=2450000.5,
                magnitude=12.3,
                magnitude_error=0.01,
                light_filter="V",
            )
            dto2 = PhotometricDataDto(
                plugin_id=plugin_id,
                julian_date=2450001.5,
                magnitude=12.4,
                magnitude_error=0.02,
                light_filter="B",
            )
            yield [dto1, dto2]

    def fake_get_plugin_instance(self, plugin_id_param):
        assert plugin_id_param == plugin_id
        return FakePlugin()

    monkeypatch.setattr(
        tasks_module.SyncTaskService,
        "get_plugin_instance",
        fake_get_plugin_instance,
        raising=True,
    )

    body = {
        "plugin_id": str(plugin_id),
        "ra_deg": 12.3,
        "dec_deg": -45.6,
        "name": "TestStar",
        "dist_arcsec": 1.23,
    }

    resp = await client.post(
        f"/tasks/submit-task/{plugin_id}/photometric-data",
        json=body,
    )

    assert resp.status_code == 200
    data = resp.json()
    task_id = uuid.UUID(data["task_id"])

    # task row should exist and be COMPLETED (set by get_photometric_data task)
    result = await db_session.execute(select(Task).where(Task.id == task_id))
    task_obj = result.scalar_one()
    assert task_obj.task_type == TaskType.photometric_data
    assert task_obj.status == TaskStatus.completed

    # PhotometricData rows inserted by SyncTaskService.bulk_insert
    result = await db_session.execute(
        select(PhotometricData).where(PhotometricData.task_id == task_id)
    )
    records = result.scalars().all()
    assert len(records) == 2

    jd_values = {r.julian_date for r in records}
    mags = {r.magnitude for r in records}
    filters = {r.light_filter for r in records}

    assert jd_values == {2450000.5, 2450001.5}
    assert mags == {12.3, 12.4}
    assert filters == {"V", "B"}
