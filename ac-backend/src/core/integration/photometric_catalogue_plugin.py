from abc import ABC, abstractmethod
from typing import TypeVar, List, Generic, AsyncGenerator
from uuid import UUID

from aiohttp import ClientSession
from astropy.coordinates import SkyCoord

from src.core.http_client import HttpClient
from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)

T = TypeVar("T", bound=StellarObjectIdentificatorDto)


class PhotometricCataloguePlugin(Generic[T], ABC):
    _http_client: ClientSession

    def __init__(self) -> None:
        self._http_client = HttpClient().get_session()
        self.__batch_limit = 20000

    def batch_limit(self):
        return self.__batch_limit

    @abstractmethod
    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncGenerator[List[T]]:
        """
        Yields chunks of found stellar objects
        :param coords:
        :param radius_arcsec:
        :param plugin_id:
        :return:
        """
        # fetch data from external catalogue in chunks
        # async for data in self._get_object_data(coords, radius_arcsec, plugin_id):
        #     # https://changyulee.oopy.io/201d939a-b8c2-8095-9430-c8d593dfdd2d
        #     loop = asyncio.get_running_loop()
        #     result = await loop.run_in_executor(None, self._process_objects_batch, data)
        #     yield result
        pass

    @abstractmethod
    async def get_photometric_data(
        self, identificator: T
    ) -> AsyncGenerator[List[PhotometricDataDto]]:
        pass
