from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, List, Generic, Iterator
from uuid import UUID

from astropy import units
from astropy.coordinates import SkyCoord, EarthLocation
from astropy.time import Time

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)

T = TypeVar("T", bound=StellarObjectIdentificatorDto)


class CatalogPlugin(Generic[T], ABC):
    def __init__(
        self, name: str, description: str, url: str, directly_identifies_objects: bool
    ) -> None:
        self.__batch_limit = 20000
        self._geocenter = EarthLocation.from_geocentric(
            0 * units.m, 0 * units.m, 0 * units.m
        )
        self._directly_identifies_objects = directly_identifies_objects
        self._description = description
        self._catalog_url = url
        self._catalog_name = name

    def batch_limit(self):
        return self.__batch_limit

    @property
    def directly_identifies_objects(self) -> bool:
        return self._directly_identifies_objects

    @property
    def description(self) -> str:
        return self._description

    @property
    def catalog_name(self) -> str:
        return self._catalog_name

    @property
    def catalog_url(self) -> str:
        return self._catalog_url

    @abstractmethod
    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[List[T]]:
        """
        Yields chunks of found stellar objects
        :param coords:
        :param radius_arcsec:
        :param plugin_id:
        :return:
        """
        pass

    @abstractmethod
    def get_photometric_data(
        self, identificator: T, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        """
        Yield chunks of photometric data for particular stellar object. Writes the original data to the provided csv file.
        :param csv_path: path to the file with raw data
        :param identificator: the stellar object to get photometric data for
        :return:
        """
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
