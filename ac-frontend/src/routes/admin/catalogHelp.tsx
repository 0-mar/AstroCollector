import {createFileRoute, Link} from "@tanstack/react-router"
import {roleGuard} from "@/features/routing/roleGuard.ts";
import {UserRoleEnum} from "@/features/common/auth/types.ts";


export const Route = createFileRoute('/admin/catalogHelp')({
    beforeLoad: roleGuard([UserRoleEnum.SUPER_ADMIN]),
    component: CatalogHelpComponent,
})


function CatalogHelpComponent() {
    const codeString = `from abc import ABC, abstractmethod
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
`
    const stellarObjectIdentificatorDtoCodeString = `class StellarObjectIdentificatorDto(BaseDto):
    """
    Represents a Data Transfer Object (DTO) for identifying stellar objects.

    This class is used to encapsulate information required for identifying stellar
    objects. Classes extending the basic identifier can add their own attributes.

    :ivar plugin_id: ID of the plugin that created this identifier.
    :ivar ra_deg: Right ascension of the stellar object, in degrees.
    :ivar dec_deg: Declination of the stellar object, in degrees.
    :ivar name: Optional name of the stellar object, if available.
    :ivar dist_arcsec: Distance from a reference point in arcseconds.
    """
    model_config = ConfigDict(extra="allow")
    plugin_id: UUID
    ra_deg: float
    dec_deg: float
    name: str | None
    dist_arcsec: float

    @field_serializer("plugin_id")
    def serialize_id(self, plugin_id: UUID, _info):
        return str(plugin_id)
    `

    const photometricDataDtoCodeString = `class PhotometricDataDto(BaseDto):
    """
    Represents photometric measurements in unified format.

    :ivar plugin_id: ID of the plugin that created this record.
    :ivar julian_date: Julian date corresponding to the observation. The timestamp must be in the BJD_TDB. PLease see _to_bjd_tdb in CatalogPlugin for more details.
    :ivar magnitude: Magnitude of the observed object.
    :ivar magnitude_error: Uncertainty associated with the magnitude.
    :ivar light_filter: Light filter applied during the observation, if available.
    """
    plugin_id: UUID
    julian_date: float
    magnitude: float
    magnitude_error: float
    light_filter: str | None`

    return (
        <div className="flex flex-col gap-2 p-8">
            <h1 className="text-3xl font-bold">Adding new catalog plugin</h1>
            <p>
                To add a new catalog plugin, one must create a Python file (module) that contains two classes: one extending the <code>StellarObjectIdentificatorDto</code> class and second one extending the <code>CatalogPlugin</code> class.
                This file has to be uploaded to the server when creating a new catalog plugin in <Link className="text-blue-600" to="/admin/catalogManagement">catalog management dashboard</Link>.
            </p>
            <h2 className="text-xl font-bold">Plugin superclass</h2>
            <p>
                Here is the code of the <code>CatalogPlugin</code> abstract class:

                <pre className="
                max-h-[50rem]
                bg-slate-900
                text-slate-50
                p-4
                rounded-lg
                text-[0.9rem]
                leading-[1.5]
                overflow-x-auto
                ">
                    <code>{codeString}</code>
                </pre>

                The class defines two important methods: <code>list_objects</code> and <code>get_photometric_data</code>.
            </p>
            <h3 className="text-lg font-bold">list_objects</h3>
            <p>
                Generator method that yields found stellar objects, which were found in the radius around the given coordinates.
                The stellar objects are identified by the corresponding <code>StellarObjectIdentificatorDto</code> subclass.
            </p>
            <h3 className="text-lg font-bold">get_photometric_data</h3>
            <p>
                Generator method that yields photometric data for a given stellar object. The object is identified via corresponding <code>StellarObjectIdentificatorDto</code> subclass.
                The data must be converted into a unified format in this method, which is explained at <code>PhotometricDataDto</code>. The original data fetched from the catalog should be written to the provided csv file.
                If the remote source returns large amounts of data, please split the data into chunks and yield each chunk. This is because the data is saved to the database,
                so that we avoid inserting too much at once. The recommended chunk size is defined in <code>batch_limit</code>.
            </p>
            <h2 className="text-xl font-bold">Stellar object identification</h2>
            <p>
                Each source needs different data to identify the stellar objects. The <code>StellarObjectIdentificatorDto</code> class defines the basic identification attributes of the stellar objects.
                The basic attributes are displayed in the stellar object selection table on the search page.
            </p>
            <pre className="
            max-h-[50rem]
            bg-slate-900
            text-slate-50
            p-4
            rounded-lg
            text-[0.9rem]
            leading-[1.5]
            overflow-x-auto
            ">
                <code>{stellarObjectIdentificatorDtoCodeString}</code>
            </pre>
            <h2 className="text-xl font-bold">Data unification</h2>
            <p>
                The photometric data fetched from the catalog must be converted into a unified format. The <code>PhotometricDataDto</code> class defines the format of the data.
            </p>
            <pre className="
            max-h-[50rem]
            bg-slate-900
            text-slate-50
            p-4
            rounded-lg
            text-[0.9rem]
            leading-[1.5]
            overflow-x-auto
            ">
                <code>{photometricDataDtoCodeString}</code>
            </pre>
            <h2 className="text-xl font-bold">Available useful packages</h2>
            <p>
                For plugin implementation, one can use the following packages:
                <ul>
                    <li>
                        <a href="https://docs.astropy.org/en/stable/index.html" target="_blank" className="text-blue-600 hover:underline">Astropy</a> - process and manipulate coordinates, time, and units. VOTable support.
                    </li>
                    <li>
                        <a href="https://astroquery.readthedocs.io/en/latest/" target="_blank" className="text-blue-600 hover:underline">Astroquery</a> - search for and retrieve photometric data from various sources
                    </li>
                    <li>
                        <a href="https://pyvo.readthedocs.io/en/latest/" target="_blank" className="text-blue-600 hover:underline">PyVO</a> - retrieve astronomical data available from archives that support standard <a href="https://www.ivoa.net/">IVOA</a> virtual observatory service protocols
                    </li>
                    <li>
                        <a href="https://www.python-httpx.org/" target="_blank" className="text-blue-600 hover:underline">httpx</a> - http client
                    </li>
                </ul>
            </p>
        </div>
    )
}
