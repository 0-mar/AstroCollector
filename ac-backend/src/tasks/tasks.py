import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID

from astropy import units
from astropy.coordinates import SkyCoord
from astropy.coordinates.name_resolve import NameResolveError
from celery.utils.log import get_task_logger
from httpx import Client
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.export.model import ExportFile
from src.tasks.service import SyncTaskService
from src.core.celery.worker import celery_app, TaskWithSession
from src.core.config.config import settings
from src.plugin.interface.schemas import StellarObjectIdentificatorDto
from src.tasks.model import StellarObjectIdentifier, PhotometricData, Task
from src.tasks.schemas import ConeSearchRequestDto, FindObjectRequestDto

from src.tasks.types import TaskStatus


logger = get_task_logger("celery_app")


def resolve_name_to_coordinates(name: str, http_client: Client) -> SkyCoord:
    """
    Resolves the given name to astronomical coordinates.

    :param http_client: http client used to query the VSX AAVSO catalog.
    :param name: The name of the stellar object to resolve.
    :type name: stellar object name to resolve the coordinates for
    :return: An object representing the resolved coordinates of the stellar object.
    """
    try:
        # resolve with CDS
        return SkyCoord.from_name(name, cache="update")
    except NameResolveError:
        # try searching in VSX AAVSO
        if name is not None:
            params = {"format": "json", "view": "api.object", "ident": name}
            query_resp = http_client.get(
                "https://vsx.aavso.org/index.php", params=params
            )
            query_data = query_resp.json()

            if query_data["VSXObject"] != []:
                record = query_data["VSXObject"]
                if "RA2000" in record and "Declination2000" in record:
                    return SkyCoord(
                        ra=record["RA2000"], dec=record["Declination2000"], unit="deg"
                    )

    raise NameResolveError(f'Object "{name}" was not found in CDS or VSX.')


def cone_search(
    plugin_id: UUID,
    task_service: SyncTaskService,
    coords: SkyCoord,
    radius_arcsec: float,
    task_id: UUID,
) -> None:
    plugin = task_service.get_plugin_instance(plugin_id)
    resources_dir = settings.RESOURCES_DIR / str(plugin_id)

    for data in plugin.list_objects(coords, radius_arcsec, plugin_id, resources_dir):
        values = [{"identifier": dto.model_dump(), "task_id": task_id} for dto in data]
        task_service.bulk_insert(values)


@celery_app.task(bind=True, base=TaskWithSession)
def catalog_cone_search(self, task_id: str, query_dict: dict[Any, Any]):
    task_service = SyncTaskService(self.session, StellarObjectIdentifier)

    try:
        task_uuid = UUID(task_id)
        query = ConeSearchRequestDto.model_validate(query_dict)
        coords = SkyCoord(
            ra=query.right_ascension_deg * units.degree,
            dec=query.declination_deg * units.degree,
            frame="icrs",
        )

        cone_search(
            plugin_id=query.plugin_id,
            task_service=task_service,
            task_id=task_uuid,
            coords=coords,
            radius_arcsec=query.radius_arcsec,
        )
    except Exception:
        logger.error(
            f"Find stellar object task with has failed (PID {os.getpid()})\nTask ID: {task_id}\nQuery: {query_dict}",
            exc_info=True,
        )
        task_service.set_task_status(task_id, TaskStatus.failed)
        raise
    else:
        logger.info(f"Cone search task {task_id} completed (PID {os.getpid()})")
        task_service.set_task_status(task_id, TaskStatus.completed)


@celery_app.task(bind=True, base=TaskWithSession)
def find_stellar_object(self, task_id: str, query_dict: dict[Any, Any]):
    task_service = SyncTaskService(self.session, StellarObjectIdentifier)
    try:
        uuid = UUID(task_id)
        query = FindObjectRequestDto.model_validate(query_dict)
        http_client = Client()
        coords = resolve_name_to_coordinates(query.name, http_client)
        http_client.close()
        cone_search(
            plugin_id=query.plugin_id,
            task_service=task_service,
            task_id=uuid,
            coords=coords,
            radius_arcsec=settings.OBJECT_SEARCH_RADIUS,
        )
    except Exception:
        logger.error(
            f"Find stellar object task with has failed (PID {os.getpid()})\nTask ID: {task_id}\nQuery: {query_dict}",
            exc_info=True,
        )
        task_service.set_task_status(task_id, TaskStatus.failed)
        raise
    else:
        logger.info(f"Find stellar object task {task_id} completed (PID {os.getpid()})")
        task_service.set_task_status(task_id, TaskStatus.completed)


@celery_app.task(bind=True, base=TaskWithSession)
def get_photometric_data(
    self, task_id: str, identificator_dict: dict[str, Any], csv_path_str: str
):
    csv_path = Path(csv_path_str)

    task_service = SyncTaskService(self.session, PhotometricData)

    try:
        identificator = StellarObjectIdentificatorDto.model_validate(identificator_dict)
        plugin = task_service.get_plugin_instance(identificator.plugin_id)
        resources_dir = settings.RESOURCES_DIR / str(identificator.plugin_id)

        for data in plugin.get_photometric_data(identificator, csv_path, resources_dir):
            values = [{**dto.model_dump(), "task_id": task_id} for dto in data]
            task_service.bulk_insert(values)
    except Exception:
        logger.error(
            f"Get photometric data task with has failed (PID {os.getpid()})\nTask ID: {task_id}\nIdentificator: {identificator_dict}",
            exc_info=True,
        )
        task_service.set_task_status(task_id, TaskStatus.failed)
        raise

    else:
        logger.info(f"Find stellar object task {task_id} completed (PID {os.getpid()})")
        task_service.set_task_status(task_id, TaskStatus.completed)


@celery_app.task(bind=True, base=TaskWithSession)
def clear_task_data(self):
    logger.info("Clearing old task data")
    session: Session = self.session

    # remove export files
    stmt = (
        select(Task.id)
        .select_from(Task)
        .where(
            Task.created_at
            < (datetime.now() - timedelta(hours=settings.TASK_DATA_DELETE_INTERVAL))
        )
    )
    try:
        result = session.execute(stmt)
        task_ids = result.scalars().all()

        for task_id in task_ids:
            csv_path = Path.joinpath(settings.TEMP_DIR, f"{task_id}.csv")

            if Path.exists(csv_path):
                logger.info(f"Removing {csv_path}")
                os.remove(csv_path)

    except Exception:
        logger.error(
            f"Clear task data task has failed (PID {os.getpid()})",
            exc_info=True,
        )
        raise

    # remove task data
    stmt = delete(Task).where(
        Task.created_at
        < (datetime.now() - timedelta(hours=settings.TASK_DATA_DELETE_INTERVAL))
    )
    try:
        session.execute(stmt)
        logger.info("Deleted expired Tasks")
    except Exception:
        logger.error(
            f"Clear task data task has failed (PID {os.getpid()})",
            exc_info=True,
        )
        raise

    else:
        logger.info(f"Clear task data completed (PID {os.getpid()})")

    stmt = (
        select(ExportFile.file_name)
        .select_from(ExportFile)
        .where(
            ExportFile.created_at
            < (datetime.now() - timedelta(hours=settings.TASK_DATA_DELETE_INTERVAL))
        )
    )
    try:
        result = session.execute(stmt)
        filenames = result.scalars().all()

        for filename in filenames:
            zip_path = settings.TEMP_DIR / filename

            if Path.exists(zip_path):
                logger.info(f"Removing {zip_path}")
                os.remove(zip_path)

    except Exception:
        logger.error(
            f"Clear task data task has failed (PID {os.getpid()})",
            exc_info=True,
        )
        raise
