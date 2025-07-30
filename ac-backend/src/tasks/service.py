import functools
from typing import Annotated
from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy import units
from fastapi import BackgroundTasks, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import insert

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
)
from src.core.repository.repository import Repository, get_repository
from src.data_retrieval.service import (
    StellarObjectIdentifierRepositoryDep,
    PhotometricDataRepositoryDep,
)
from src.tasks.model import StellarObjectIdentifier, PhotometricData, Task
from src.tasks.schemas import ConeSearchRequestDto, FindObjectRequestDto
from src.plugin.router import PluginServiceDep
from src.tasks.types import TaskStatus

OBJECT_SEARCH_RADIUS = 30

TaskRepositoryDep = Annotated[
    Repository[Task],
    Depends(get_repository(Task)),
]


class StellarObjectService:
    def __init__(
        self,
        plugin_service: PluginServiceDep,
        soi_repository: StellarObjectIdentifierRepositoryDep,
        pd_repository: PhotometricDataRepositoryDep,
        task_repository: TaskRepositoryDep,
        background_tasks: BackgroundTasks,
    ) -> None:
        self._plugin_service = plugin_service
        self._soi_repository = soi_repository
        self._pd_repository = pd_repository
        self._task_repository = task_repository
        self._background_tasks = background_tasks

    async def _bulk_insert(self, session, data, mapping, task_id, table):
        values = await run_in_threadpool(
            lambda: [mapping(task_id, dto) for dto in data]
        )
        stmt = insert(table)
        await session.execute(stmt, values)
        await session.commit()

    @staticmethod
    def _task(f):
        @functools.wraps(f)
        async def wrapper(self, *args, **kwargs):
            print("fds")
            task: Task = await self._task_repository.save(Task())
            self._background_tasks.add_task(f, self, task.id, *args, **kwargs)

            return task.id

        return wrapper

    @staticmethod
    def _task_status(f):
        @functools.wraps(f)
        async def wrapper(self, task_id, *args, **kwargs):
            print(f"tady {task_id}")
            try:
                await f(self, task_id, *args, **kwargs)
            except Exception:
                print("chyba")

                result = await self._task_repository.update(
                    task_id, {"status": TaskStatus.failed}
                )
                print(result)
                # TODO log error
            else:
                print("fdastady")

                await self._task_repository.update(
                    task_id, {"status": TaskStatus.completed}
                )

        return wrapper

    async def _resolve_name_to_coordinates(self, name: str) -> SkyCoord:
        """
        Resolves the given name to astronomical coordinates.

        :param name: The name of the celestial object to resolve.
        :type name: str
        :return: An object representing the resolved coordinates of the celestial object.
        :rtype: SkyCoord
        """
        # TODO add other coordinate resolving options (e.g. from astroquery etc.)
        # NameResolveError is raised when we cant resolve the coords
        coords = await run_in_threadpool(SkyCoord.from_name, name, cache="update")
        return coords

    async def __cone_search(
        self,
        plugin_id: UUID,
        coords: SkyCoord,
        radius_arcsec: float,
        task_id: UUID,
        discriminator: str,
    ) -> None:
        plugin_dto = await self._plugin_service.get_plugin(plugin_id)
        plugin = await self._plugin_service.get_plugin_instance(plugin_dto.id)

        session = self._soi_repository.session()
        async for data in plugin.list_objects(coords, radius_arcsec, plugin_id):
            await self._bulk_insert(
                session,
                data,
                lambda t_id, dto: {
                    "type": discriminator,
                    "task_id": t_id,
                    "identifier": dto.model_dump(),
                },
                task_id,
                StellarObjectIdentifier,
            )

    @_task
    @_task_status
    async def catalogue_cone_search(self, task_id: UUID, query: ConeSearchRequestDto):
        """
        Performs cone search on a catalogue, identified by query.plugin_id
        :param task_id:
        :param query:
        :return: list of stellar objects search results
        """
        coords = SkyCoord(
            ra=query.right_ascension_deg * units.degree,
            dec=query.declination_deg * units.degree,
            frame="icrs",
        )

        await self.__cone_search(query.plugin_id, coords, query.radius_arcsec, task_id)

    @_task
    @_task_status
    async def find_stellar_object(self, task_id: UUID, query: FindObjectRequestDto):
        """
        Given a stellar object name, return all matches within radius of 30 arcsec.
        :param task_id:
        :param query:
        :return: list of stellar objects search results
        """
        coords = await self._resolve_name_to_coordinates(query.name)
        await self.__cone_search(query.plugin_id, coords, OBJECT_SEARCH_RADIUS, task_id)

    @_task
    @_task_status
    async def get_photometric_data(
        self, task_id: UUID, identificator_model: StellarObjectIdentificatorDto
    ) -> None:
        """
        Retrieve photometric data for a given object using the corresponding plugin.
        :param task_id:
        :param plugin_id:
        :param identificator_model:
        :return:
        """
        plugin = await self._plugin_service.get_plugin_instance(
            identificator_model.plugin_id
        )
        session = self._pd_repository.session()
        async for data in plugin.get_photometric_data(identificator_model):
            await self._bulk_insert(
                session,
                data,
                lambda t_id, dto: {"task_id": t_id, **dto.model_dump()},
                task_id,
                PhotometricData,
            )

    async def get_task_status(self, task_id: UUID) -> TaskStatus:
        task = await self._task_repository.get(task_id)
        return task.status
