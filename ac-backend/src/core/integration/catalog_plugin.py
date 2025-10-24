from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, List, Generic, Iterator, Literal
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
        Yield chunks of photometric data for particular stellar object. Writes the original (raw) data to the provided csv file.
        :param csv_path: path to store the original data
        :param identificator: the stellar object to get photometric data for
        :return:
        """
        pass

    def _to_bjd_tdb(
        self,
        time_value: float,
        time_format: str,
        time_scale: str,
        reference_frame: Literal["geocentric", "heliocentric", "barycentric"],
        ra_deg: float,
        dec_deg: float,
    ) -> float:
        """
        Converts given time value in given format (e. g. julian date) in given time standard (e. g. utc, tcb, tdb) in given reference frame (e. g. geocentric, heliocentric) to BJD_TDB timestamp.
        The time standard is referred to as the time_scale.

        As defined in:

        https://ui.adsabs.harvard.edu/abs/2010PASP..122..935E/abstract

        - “reference frame” - geometric location from which one could measure time (different reference frames differ by the light-travel time between them)
        - “time standard” – the way a particular clock ticks and its arbitrary zero point, as defined by international standards; Here referred to as the time_scale
        - “time stamp” - the combination of the two, and determines the timing accuracy of the event.

        To choose appropriate time format, time scale and reference frame, please consult the catalog documentation.

        :param time_value: The time value to convert.
        :param time_format: The format of the time value.
        :param time_scale: The time standard of the time value.
        :param reference_frame: The location reference frame of the time value.
        :param ra_deg: Right ascension of the target in degrees.
        :param dec_deg: Declination of the target in degrees.
        :return: Timestamp in BJD_TDB format. reference frame = barycentre, time standard = tdb.
        """

        time = Time(time_value, format=time_format, scale=time_scale)
        target = SkyCoord(ra_deg, dec_deg, unit="deg")

        if reference_frame == "barycentric":
            # already in barycentric frame; just return it.
            return time.tdb.jd

        if reference_frame == "heliocentric":
            ltt_helio = time.light_travel_time(
                target, kind="heliocentric", location=self._geocenter
            )
            ltt_bary = time.light_travel_time(
                target, kind="barycentric", location=self._geocenter
            )
            corrected_time = time - ltt_helio + ltt_bary

            return corrected_time.tdb.jd

        if reference_frame == "geocentric":
            ltt_bary = time.light_travel_time(
                target, kind="barycentric", location=self._geocenter
            )
            corrected_time = time + ltt_bary

            return corrected_time.tdb.jd

        raise ValueError(
            f"Invalid reference frame {reference_frame}. Valid values are: geocentric, heliocentric, barycentric."
        )
