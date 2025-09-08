from abc import ABC, abstractmethod
from typing import TypeVar, List, Generic, AsyncGenerator
from uuid import UUID

from aiohttp import ClientSession
from astropy import units
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time

from src.core.http_client import HttpClient
from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)

T = TypeVar("T", bound=StellarObjectIdentificatorDto)


class CatalogPlugin(Generic[T], ABC):
    _http_client: ClientSession

    def __init__(self) -> None:
        self._http_client = HttpClient().get_session()
        self.__batch_limit = 20000
        self._geocenter = EarthLocation.from_geocentric(
            0 * units.m, 0 * units.m, 0 * units.m
        )
        self._directly_identifies_objects = True

    def batch_limit(self):
        return self.__batch_limit

    @property
    def directly_identifies_objects(self) -> bool:
        return self._directly_identifies_objects

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

    def _to_bjd(
        self,
        time_value: float,
        format: str,
        scale: str,
        ra_deg: float,
        dec_deg: float,
        is_hjd: bool,
    ) -> float:
        # convert JD_UTC to BJD_TDB
        time = Time(time_value, format=format, scale=scale)
        target = SkyCoord(ra_deg, dec_deg, unit="deg")
        ltt_bary = time.light_travel_time(
            target, kind="barycentric", location=self._geocenter
        )

        if is_hjd:
            ltt_helio = time.light_travel_time(
                target, kind="heliocentric", location=self._geocenter
            )
            ltt_bary = ltt_bary - ltt_helio

        bjd_tdb = time.tdb + ltt_bary
        return bjd_tdb.jd
