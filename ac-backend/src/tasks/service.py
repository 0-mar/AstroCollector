import asyncio
from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy import units
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import insert

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
)
from src.data_retrieval.service import (
    StellarObjectIdentifierRepositoryDep,
    PhotometricDataRepositoryDep,
)
from src.tasks.model import StellarObjectIdentifier, PhotometricData
from src.tasks.schemas import ConeSearchRequestDto, FindObjectRequestDto
from src.plugin.router import PluginServiceDep

OBJECT_SEARCH_RADIUS = 30


class StellarObjectService:
    def __init__(
        self,
        plugin_service: PluginServiceDep,
        soi_repository: StellarObjectIdentifierRepositoryDep,
        pd_repository: PhotometricDataRepositoryDep,
    ) -> None:
        self._plugin_service = plugin_service
        self._soi_repository = soi_repository
        self._pd_repository = pd_repository

    async def _bulk_insert(self, session, data, mapping, task_id, table):
        loop = asyncio.get_running_loop()
        values = await loop.run_in_executor(
            None,
            lambda data_list, map_fn: [map_fn(task_id, dto) for dto in data_list],
            data,
            mapping,
        )
        stmt = insert(table)
        await session.execute(stmt, values)
        await session.commit()

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
        self, plugin_id: UUID, coords: SkyCoord, radius_arcsec: float, task_id: UUID
    ) -> None:
        plugin_dto = await self._plugin_service.get_plugin(plugin_id)
        plugin = await self._plugin_service.get_plugin_instance(plugin_dto.id)
        session = self._soi_repository.session()
        async for data in plugin.cone_search(coords, radius_arcsec, plugin_id):
            await self._bulk_insert(
                session,
                data,
                lambda t_id, dto: {"task_id": t_id, "identifier": dto.model_dump()},
                task_id,
                StellarObjectIdentifier,
            )

    async def catalogue_cone_search(self, query: ConeSearchRequestDto) -> None:
        """
        Performs cone search on a catalogue, identified by query.plugin_id
        :param query:
        :return: list of stellar objects search results
        """
        coords = SkyCoord(
            ra=query.right_ascension_deg * units.degree,
            dec=query.declination_deg * units.degree,
            frame="icrs",
        )

        await self.__cone_search(query.plugin_id, coords, query.radius_arcsec)

    async def find_stellar_object(self, query: FindObjectRequestDto) -> None:
        """
        Given a stellar object name, return all matches within radius of 30 arcsec.
        :param query:
        :return: list of stellar objects search results
        """
        coords = await self._resolve_name_to_coordinates(query.name)
        await self.__cone_search(query.plugin_id, coords, OBJECT_SEARCH_RADIUS)

    async def get_photometric_data(
        self, identificator_model: StellarObjectIdentificatorDto, task_id: UUID
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
        async for data in plugin.lightcurve_data(identificator_model):
            await self._bulk_insert(
                session,
                data,
                lambda t_id, dto: {"task_id": t_id, **dto.model_dump()},
                task_id,
                PhotometricData,
            )
