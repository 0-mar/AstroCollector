from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy import units
from fastapi.concurrency import run_in_threadpool

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)
from src.data_retriever.schemas import ConeSearchRequestDto, FindObjectRequestDto
from src.plugin.router import PluginServiceDep

OBJECT_SEARCH_RADIUS = 30


class StellarObjectService:
    def __init__(self, plugin_service: PluginServiceDep):
        self._plugin_service = plugin_service

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
        self, plugin_id: UUID, coords: SkyCoord, radius_arcsec: float
    ) -> list[StellarObjectIdentificatorDto]:
        plugin_dto = await self._plugin_service.get_plugin(plugin_id)
        plugin = await self._plugin_service.get_plugin_instance(plugin_dto.id)
        return await plugin.list_objects(coords, radius_arcsec, plugin_dto.id)

    async def catalogue_cone_search(
        self, query: ConeSearchRequestDto
    ) -> list[StellarObjectIdentificatorDto]:
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

        return await self.__cone_search(query.plugin_id, coords, query.radius_arcsec)

    async def find_stellar_object(
        self, query: FindObjectRequestDto
    ) -> list[StellarObjectIdentificatorDto]:
        """
        Given a stellar object name, return all matches within radius of 30 arcsec.
        :param query:
        :return: list of stellar objects search results
        """
        coords = await self._resolve_name_to_coordinates(query.name)
        return await self.__cone_search(query.plugin_id, coords, OBJECT_SEARCH_RADIUS)

    async def get_photometric_data(
        self, identificator_model: StellarObjectIdentificatorDto
    ) -> list[PhotometricDataDto]:
        """
        Retrieve photometric data for a given object using the corresponding plugin.
        :param plugin_id:
        :param identificator_model:
        :return:
        """
        plugin = await self._plugin_service.get_plugin_instance(
            identificator_model.plugin_id
        )
        return await plugin.get_photometric_data(identificator_model)

    async def get_photometric_data_multiple_sources(
        self, identifiers: list[StellarObjectIdentificatorDto]
    ) -> dict[UUID, list[PhotometricDataDto]]:
        """
        Retrieve photometric data for a given object using multiple plugins.
        :param identifiers:
        :return:
        """

        result: dict[UUID, list[PhotometricDataDto]] = {}

        for identificator_model in identifiers:
            data = await self.get_photometric_data(identificator_model)
            result[identificator_model.plugin_id] = data

        return result
