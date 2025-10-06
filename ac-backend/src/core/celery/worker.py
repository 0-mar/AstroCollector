import os
from typing import Any
from uuid import UUID

from astropy import units
from astropy.coordinates import SkyCoord
from celery import Celery
from celery.signals import worker_process_init
from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import Session

from src.celery.sync_tasks import SyncTaskService
from src.core.config.config import settings
from src.core.integration.schemas import StellarObjectIdentificatorDto
from src.tasks.model import StellarObjectIdentifier
from src.tasks.schemas import ConeSearchRequestDto, FindObjectRequestDto
from celery.utils.log import get_task_logger

from src.tasks.types import TaskStatus

# Initialize Celery with Redis as broker and result backend
celery_app = Celery(
    "ac_worker",
    broker=f"redis://redis:{settings.CACHE_PORT}/0",
    backend=f"redis://redis:{settings.CACHE_PORT}/0",
)
# Celery configuration for reliability and performance
celery_app.conf.update(
    result_expires=settings.TASK_DATA_DELETE_INTERVAL
    * 3600,  # Task results expire in 1 hour (cleanup)
    task_track_started=True,  # Enable tracking the STARTED state of tasks
    task_acks_late=True,  # Acknowledge tasks after execution, not before
    # task_reject_on_worker_lost=True,   # Reschedule task if worker crashes:contentReference[oaicite:19]{index=19}
    worker_prefetch_multiplier=1,  # Each worker grabs only 1 task at a time:contentReference[oaicite:20]{index=20}
)

logger = get_task_logger(__name__)

# connection pooling when forking processes:
# https://docs.sqlalchemy.org/en/20/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork

# the engine is contained in all forked processes
engine = create_engine(
    settings.SYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


@worker_process_init.connect
def init_worker_process(*args, **kwargs):
    """
    Initialize resources for a worker process.

    This signal handler runs in each forked child process.

    Ensure the parent proc's database connections are not touched
    in the new connection pool
    """
    engine.dispose(close=False)


# tests for connections being shared across process boundaries, and invalidates them:
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    connection_record.info["pid"] = os.getpid()


@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    pid = os.getpid()
    if connection_record.info["pid"] != pid:
        connection_record.dbapi_connection = connection_proxy.dbapi_connection = None
        raise exc.DisconnectionError(
            "Connection record belongs to pid %s, "
            "attempting to check out in pid %s" % (connection_record.info["pid"], pid)
        )


class TaskWithSession(celery_app.Task):
    """
    Task with ready to go session object
    https://celery.school/sqlalchemy-session-celery-tasks
    """

    def __init__(self):
        self._session: Session | None = None

    def before_start(self, task_id, args, kwargs):
        self._session = Session(bind=engine, autocommit=False, expire_on_commit=False)
        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        self._session.close()
        self._session = None
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    @property
    def session(self):
        return self._session


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
            radius_arcsec=query.radius_arcsec,
        )
    except Exception:
        logger.error(
            f"Find stellar object task with has failed (PID {os.getpid()})\nTask ID: {task_id}\nQuery: {query_dict}",
            exc_info=True,
        )
        task_service.set_task_status(task_id, TaskStatus.failed)
    else:
        logger.info(f"Find stellar object task {task_id} completed (PID {os.getpid()})")
        task_service.set_task_status(task_id, TaskStatus.completed)


@celery_app.task(bind=True, base=TaskWithSession)
def get_photometric_data(
    self, task_id: str, identificator_dict: StellarObjectIdentificatorDto
):
    task_service = SyncTaskService(self.session, StellarObjectIdentifier)

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
    else:
        logger.info(f"Find stellar object task {task_id} completed (PID {os.getpid()})")
        task_service.set_task_status(task_id, TaskStatus.completed)
