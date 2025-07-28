import asyncio
from abc import ABC, abstractmethod
from typing import TypeVar, List, Generic, AsyncIterator, Any, Iterator
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
        self.__batch_limit = 5000

    def batch_limit(self):
        return self.__batch_limit

    # @abstractmethod
    async def _get_object_data(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncIterator[Any]:
        """
        Get single chunk of stellar object data
        :param coords:
        :param radius_arcsec:
        :param plugin_id:
        :return:
        """
        pass

    # @abstractmethod
    def _process_object_data(self, data_chunk: Any) -> Iterator[List[T]]:
        pass

    @abstractmethod
    async def cone_search(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncIterator[List[T]]:
        # fetch data from external catalogue in chunks
        # async for data in self._get_object_data(coords, radius_arcsec, plugin_id):
        # https://changyulee.oopy.io/201d939a-b8c2-8095-9430-c8d593dfdd2d
        # loop = asyncio.get_running_loop()
        # result = await loop.run_in_executor(None, self._process_object_data, data)
        # yield result
        #
        # async for processed_data in loop.run_in_executor(None, self._process_object_data, data):
        #     (async for loop.run_in_executor(None, self._process_object_data, data))

        # def generator():
        #     yield from self._process_object_data(data)
        #
        # gen = generator()
        #
        # while True:
        #     try:
        #         processed_data = await loop.run_in_executor(None, next, gen)
        #         yield processed_data
        #     except StopIteration:
        #         break
        pass

    # @abstractmethod
    def _process_photometric_data(self, data_chunk: Any) -> List[PhotometricDataDto]:
        pass

    # @abstractmethod
    async def _get_photometric_data(self, identificator: T) -> AsyncIterator[Any]:
        pass

    @abstractmethod
    async def lightcurve_data(
        self, identificator: T
    ) -> AsyncIterator[List[PhotometricDataDto]]:
        async for data in self._get_photometric_data(identificator):
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None, self._process_photometric_data, data
            )
            yield result
