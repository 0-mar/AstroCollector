import functools
import logging
from uuid import UUID

from astropy import units
from astropy.coordinates import SkyCoord
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.database import async_sessionmanager
from src.core.integration.schemas import StellarObjectIdentificatorDto
from src.core.repository.exception import IntegrityException
from src.core.repository.repository import Repository
from src.plugin.model import Plugin
from src.plugin.service import PluginService
from src.tasks.model import Task, StellarObjectIdentifier, PhotometricData
from src.tasks.schemas import ConeSearchRequestDto, FindObjectRequestDto
from src.tasks.types import TaskStatus

logger = logging.getLogger(__name__)

OBJECT_SEARCH_RADIUS = 30


def task_status(f):
    @functools.wraps(f)
    async def wrapper(task_id, *args, **kwargs):
        async with async_sessionmanager.session() as session:
            task_repository = Repository(Task, session)
            try:
                await f(task_id, session, *args, **kwargs)
            except Exception:
                await task_repository.update(task_id, {"status": TaskStatus.failed})
                logger.error(f"Task {task_id} failed", exc_info=True)
                # raise
            else:
                logger.info(f"Task {task_id} completed")
                await task_repository.update(task_id, {"status": TaskStatus.completed})

    return wrapper


async def resolve_name_to_coordinates(name: str) -> SkyCoord:
    """
    Resolves the given name to astronomical coordinates.

    :param name: The name of the stellar object to resolve.
    :type name: str
    :return: An object representing the resolved coordinates of the stellar object.
    :rtype: SkyCoord
    """
    # TODO add other coordinate resolving options (e.g. from astroquery etc.)
    # NameResolveError is raised when we cant resolve the coords
    coords = await run_in_threadpool(SkyCoord.from_name, name, cache="update")
    return coords


async def cone_search(
    plugin_id: UUID,
    session: AsyncSession,
    coords: SkyCoord,
    radius_arcsec: float,
    task_id: UUID,
) -> None:
    plugin_service = PluginService(Repository(Plugin, session))
    soi_repository = Repository(StellarObjectIdentifier, session)

    plugin_dto = await plugin_service.get_plugin(plugin_id)
    plugin = await plugin_service.get_plugin_instance(plugin_dto.id)

    async for data in plugin.list_objects(coords, radius_arcsec, plugin_id):
        values = await run_in_threadpool(
            lambda: [
                StellarObjectIdentifier(identifier=dto.model_dump(), task_id=task_id)
                for dto in data
            ]
        )
        try:
            await soi_repository.bulk_insert(values)
        except IntegrityException:
            logger.warning(
                "Task was already deleted - did it take too long to complete it?",
                exc_info=True,
            )
            break


@task_status
async def catalog_cone_search(
    task_id: UUID, session: AsyncSession, query: ConeSearchRequestDto
):
    """
    Performs cone search on a catalogue, identified by query.plugin_id
    :param session:
    :param task_id:
    :param query:
    :return: list of stellar objects search results
    """
    coords = SkyCoord(
        ra=query.right_ascension_deg * units.degree,
        dec=query.declination_deg * units.degree,
        frame="icrs",
    )

    await cone_search(query.plugin_id, session, coords, query.radius_arcsec, task_id)


@task_status
async def find_stellar_object(
    task_id: UUID, session: AsyncSession, query: FindObjectRequestDto
):
    """
    Given a stellar object name, return all matches within radius of 30 arcsec.
    :param session:
    :param task_id:
    :param query:
    :return: list of stellar objects search results
    """
    coords = await resolve_name_to_coordinates(query.name)
    await cone_search(query.plugin_id, session, coords, OBJECT_SEARCH_RADIUS, task_id)


@task_status
async def get_photometric_data(
    task_id: UUID,
    session: AsyncSession,
    identificator_model: StellarObjectIdentificatorDto,
) -> None:
    """
    Retrieve photometric data for a given object using the corresponding plugin.
    :param task_id:
    :param plugin_id:
    :param identificator_model:
    :return:
    """
    plugin_service = PluginService(Repository(Plugin, session))
    pd_repository = Repository(PhotometricData, session)

    plugin = await plugin_service.get_plugin_instance(identificator_model.plugin_id)

    async for data in plugin.get_photometric_data(identificator_model):
        values = await run_in_threadpool(
            lambda: [
                PhotometricData(**dto.model_dump(), task_id=task_id) for dto in data
            ]
        )
        try:
            await pd_repository.bulk_insert(values)
        except IntegrityException:
            logger.warning(
                "Task was already deleted - did it take too long to complete it?",
                exc_info=True,
            )
            break
