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
    """
    Base class for all catalog plugins.
    """

    def __init__(
        self, name: str, description: str, url: str, directly_identifies_objects: bool
    ) -> None:
        """
        Create new catalog plugin.
        :param name: name of the catalog
        :param description: catalog description
        :param url: catalog website url
        :param directly_identifies_objects: whether the catalog directly identifies objects or not.
        That is, is each photometry record linked to an object with ID, or does the catalog just provide a list of measurements for given position?
        """
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
        Generator method that yields found stellar objects. Returns plugins corresponding stellar object identificators
        found in the radius around the given coordinates.
        :param coords: the coordinates which to search for objects around
        :param radius_arcsec: search radius around the given coordinates in arcseconds
        :param plugin_id: the plugin id of the used plugin database entity. Used to identify the plugin in the database.
        :return: list of stellar object identificators.
        """
        pass

    @abstractmethod
    def get_photometric_data(
        self, identificator: T, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        """
        Generator method that yields photometric data for a given stellar object. Writes the original fetched data to the provided csv file.

        The data has to be converted into a unified format in this method. Please see PhotometricDataDto for format details. For timestamp unification, please use the _to_bjd_tdb helper method.

        If the remote source returns large amounts of data, please split the data into chunks and yield each chunk. This is because the data is saved to the database,
        so that we avoid inserting too much at once. The recommended chunk size is defined in batch_limit.

        :param csv_path: path to store the original data
        :param identificator: the stellar object to get photometric data for
        :return: list of photometric data for the given stellar object.
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
