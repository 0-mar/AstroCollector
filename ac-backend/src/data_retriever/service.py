from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy import units
from fastapi.concurrency import run_in_threadpool

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)
from src.data_retriever.schemas import SearchQueryRequestDto, FindObjectQueryRequestDto
from src.plugin.router import PluginServiceDep

OBJECT_SEARCH_RADIUS = 10


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
        coords = await run_in_threadpool(SkyCoord.from_name, name, cache="update")
        return coords

    async def search_catalogues_by_coords(
        self, query: SearchQueryRequestDto
    ) -> dict[UUID, list[StellarObjectIdentificatorDto]]:
        """
        For all catalogues, search for objects within the given radius.
        :param query: Sky coordinates of the celestial object (ICRS format, degrees) and radius to search around.
        :return: Dictionary of catalogues and their corresponding objects. Key is the catalogues ID.
        """
        coords = SkyCoord(
            ra=query.right_ascension_deg * units.degree,
            dec=query.declination_deg * units.degree,
            frame="icrs",
        )

        plugins = await self._plugin_service.list_plugins()
        result: dict[UUID, list[StellarObjectIdentificatorDto]] = {}
        for plugin_dto in plugins:
            plugin = await self._plugin_service.get_plugin_instance(plugin_dto.id)
            objects = await plugin.list_objects(
                coords.ra.degree, coords.dec.degree, query.radius_arcsec, plugin_dto.id
            )
            result[plugin_dto.id] = objects

        return result

    async def find_stellar_object_in_catalogues(
        self, query: FindObjectQueryRequestDto
    ) -> dict[UUID, StellarObjectIdentificatorDto]:
        """
        Given a stellar object name, return the closest match in all catalogues.
        :param query:
        :return:
        """
        coords = await self._resolve_name_to_coordinates(query.name)
        plugins = await self._plugin_service.list_plugins()
        result: dict[UUID, StellarObjectIdentificatorDto] = {}
        for plugin_dto in plugins:
            plugin = await self._plugin_service.get_plugin_instance(plugin_dto.id)
            stellar_objects = await plugin.list_objects(
                coords.ra.degree, coords.dec.degree, OBJECT_SEARCH_RADIUS, plugin_dto.id
            )

            # object was found
            if stellar_objects != []:
                # TODO: which one to pick from the list?
                result[plugin_dto.id] = stellar_objects[0]

        return result

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
