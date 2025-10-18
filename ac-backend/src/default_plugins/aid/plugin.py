from pathlib import Path
from typing import Any, Iterator
from uuid import UUID

from astropy.coordinates import SkyCoord
import pandas as pd

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)
import httpx


class AidIdentificatorDto(StellarObjectIdentificatorDto):
    auid: str


class AidPlugin(CatalogPlugin[AidIdentificatorDto]):
    """
    Integration of the AID plugin
    """

    def __init__(self) -> None:
        super().__init__(
            "AAVSO",
            "The AAVSO International Database has over 54 million variable star observations going back over one hundred years. It is the largest and most comprehensive digital variable star database in the world. Over 1,000,000 new variable star brightness measurements are added to the database every year by over 700 observers from all over the world.",
            "https://www.aavso.org/aavso-international-database",
            True,
        )
        self._http_client = httpx.Client()

    def __list_url(self, ra: float, dec: float, radius: float) -> str:
        return f"https://vsx.aavso.org/index.php?view=api.list&ra={ra}&dec={dec}&radius={radius}&format=json"

    def __data_url(self, auid: str) -> str:
        return (
            f"https://vsx.aavso.org/index.php?view=api.delim&ident={auid}&delimiter=;;;"
        )

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[AidIdentificatorDto]]:
        response = self._http_client.get(
            self.__list_url(coords.ra.deg, coords.dec.deg, radius_arcsec / 3600.0)
        )
        query_data = response.json()
        yield self._process_objects(query_data, plugin_id, coords)

    def _process_objects(
        self, query_data: dict[str, Any], plugin_id: UUID, search_coords: SkyCoord
    ) -> list[AidIdentificatorDto]:
        results = []
        if query_data["VSXObjects"] == []:
            return results

        for record in query_data["VSXObjects"]["VSXObject"]:
            if "AUID" not in record:
                continue
            record_coords = SkyCoord(
                record["RA2000"], record["Declination2000"], unit="deg"
            )
            results.append(
                AidIdentificatorDto(
                    plugin_id=plugin_id,
                    auid=record["AUID"],
                    ra_deg=record["RA2000"],
                    dec_deg=record["Declination2000"],
                    name=record["Name"] if "Name" in record else "",
                    dist_arcsec=search_coords.separation(record_coords).arcsec,
                )
            )

        return results

    def get_photometric_data(
        self, identificator: AidIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        self.__write_to_csv(self.__data_url(identificator.auid), csv_path)

        # release data in chunks
        for chunk in self.__get_chunk(csv_path, identificator):
            if chunk == []:
                continue

            yield chunk

    def __write_to_csv(self, url: str, path: Path) -> None:
        with self._http_client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_bytes(1024 * 1024):
                    f.write(chunk)

    def __get_chunk(
        self, path: Path, identificator: AidIdentificatorDto
    ) -> Iterator[list[PhotometricDataDto]]:
        for chunk in pd.read_csv(
            path,
            chunksize=50_000,
            sep=";;;",
            engine="python",
            usecols=["JD", "mag", "uncert", "band"],
            dtype={
                "JD": "float64",
                "mag": "float64",
                "uncert": "float64",
                "band": "str",
            },
            na_values=(""),
            on_bad_lines="skip",
        ):
            batch: list[PhotometricDataDto] = []
            chunk = chunk.dropna(subset=["JD", "mag", "uncert", "band"])
            for jd, mag, uncert, band in chunk.itertuples(index=False, name=None):
                # convert JD_UTC to BJD_TDB
                bjd = self._to_bjd(
                    jd,
                    format="jd",
                    scale="utc",
                    ra_deg=identificator.ra_deg,
                    dec_deg=identificator.dec_deg,
                    is_hjd=False,
                )

                batch.append(
                    PhotometricDataDto(
                        plugin_id=identificator.plugin_id,
                        julian_date=bjd,
                        magnitude=mag,
                        magnitude_error=uncert,
                        light_filter=band,
                    )
                )
            yield batch
