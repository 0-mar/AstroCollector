import logging
import os
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from astropy import units
from astropy.coordinates import SkyCoord
from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.tasks.service import SyncTaskService
from src.core.celery.worker import celery_app, TaskWithSession
from src.core.config.config import settings
from src.core.integration.schemas import StellarObjectIdentificatorDto
from src.tasks.model import StellarObjectIdentifier, PhotometricData, Task
from src.tasks.schemas import ConeSearchRequestDto, FindObjectRequestDto

from src.tasks.types import TaskStatus


# logger = get_task_logger(__name__)
logger = logging.getLogger(__name__)


def resolve_name_to_coordinates(name: str) -> SkyCoord:
    """
    Resolves the given name to astronomical coordinates.

    :param name: The name of the stellar object to resolve.
    :type name: str
    :return: An object representing the resolved coordinates of the stellar object.
    :rtype: SkyCoord
    """
    # TODO add other coordinate resolving options (e.g. from astroquery etc.)
    # NameResolveError is raised when we cant resolve the coords
    return SkyCoord.from_name(name, cache="update")


def cone_search(
    plugin_id: UUID,
    task_service: SyncTaskService,
    coords: SkyCoord,
    radius_arcsec: float,
    task_id: UUID,
) -> None:
    plugin = task_service.get_plugin_instance(plugin_id)

    for data in plugin.list_objects(coords, radius_arcsec, plugin_id):
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
        coords = resolve_name_to_coordinates(query.name)
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
    self, task_id: str, identificator_dict: StellarObjectIdentificatorDto
):
    task_service = SyncTaskService(self.session, PhotometricData)

    try:
        identificator = StellarObjectIdentificatorDto.model_validate(identificator_dict)
        plugin = task_service.get_plugin_instance(identificator.plugin_id)

        for data in plugin.get_photometric_data(identificator):
            values = [{**dto.model_dump(), "task_id": task_id} for dto in data]
            task_service.bulk_insert(values)
    except Exception:
        logger.error(
            f"Find stellar object task with has failed (PID {os.getpid()})\nTask ID: {task_id}\nIdentificator: {identificator_dict}",
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

    stmt = delete(Task).where(
        Task.created_at
        < (datetime.now() - timedelta(hours=settings.TASK_DATA_DELETE_INTERVAL))
    )
    session: Session = self.session
    try:
        session.execute(stmt)
    except Exception:
        logger.error(
            f"Clear task data task has failed (PID {os.getpid()})",
            exc_info=True,
        )
        raise

    else:
        logger.info(f"Clear task data completed (PID {os.getpid()})")
