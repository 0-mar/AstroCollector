from pathlib import Path
from typing import Iterator
from uuid import UUID

import httpx
import pandas as pd
from astropy.coordinates import SkyCoord

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)
from bs4 import BeautifulSoup


class CatalinaIdentificatorDto(StellarObjectIdentificatorDto):
    csv_link: str


class CatalinaPlugin(CatalogPlugin[CatalinaIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "Catalina",
            "The Catalina Surveys consists of all photometry from seven years of photometry taken with the the CSS telescopes. This data release encompasses the photometry for 500 million objects (~40 billion measurements) with V magnitudes between 11.5 and 21.5 from an area of 33,000 square degrees.",
            "http://nesssi.cacr.caltech.edu/DataRelease/",
            False,
        )
        self._http_client = httpx.Client(timeout=10.0)
        self._url = "http://nunuku.caltech.edu/cgi-bin/getcssconedb_release_img.cgi"

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[CatalinaIdentificatorDto]]:
        form_data = {
            "RADec": f"{coords.ra.deg} {coords.dec.deg}",
            "Rad": f"{radius_arcsec / 60}",
            "IMG": "nun",
            "DB": "photcat",
            ".submit": "Submit",
            "OUT": "csv",
            "SHORT": "short",
            "PLOT": "plot",
        }

        resp = self._http_client.post(self._url, data=form_data)
        resp.raise_for_status()
        html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        a_element = soup.find(
            "a", string=lambda s: s and s.strip().lower() == "download"
        )

        # no results were found
        if a_element is None:
            return

        csv_link = a_element["href"]
        yield [
            CatalinaIdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=coords.ra.deg,
                dec_deg=coords.dec.deg,
                name=None,
                dist_arcsec=0,
                csv_link=csv_link,
            )
        ]

    def get_photometric_data(
        self, identificator: CatalinaIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        self.__write_to_csv(identificator.csv_link, csv_path)

        # release data in chunks
        for chunk in self.__get_chunk(csv_path, identificator):
            if chunk == []:
                continue

            yield chunk

    def __get_chunk(
        self, path: Path, identificator: CatalinaIdentificatorDto
    ) -> Iterator[list[PhotometricDataDto]]:
        for chunk in pd.read_csv(
            path,
            chunksize=50_000,
            sep=",",
            engine="python",
            usecols=["MJD", "Mag", "Magerr"],
            dtype={
                "MJD": "float64",
                "Mag": "float64",
                "Magerr": "float64",
            },
            na_values=(""),
            on_bad_lines="skip",
        ):
            batch: list[PhotometricDataDto] = []
            chunk = chunk.dropna(subset=["MJD", "Mag", "Magerr"])
            for mjd, mag, magerr in chunk.itertuples(index=False, name=None):
                # convert MJD_UTC to BJD_TDB
                bjd = self._to_bjd_tdb(
                    mjd,
                    time_format="mjd",
                    time_scale="utc",
                    reference_frame="geocentric",
                    ra_deg=identificator.ra_deg,
                    dec_deg=identificator.dec_deg,
                )

                batch.append(
                    PhotometricDataDto(
                        plugin_id=identificator.plugin_id,
                        julian_date=bjd,
                        magnitude=mag,
                        magnitude_error=magerr,
                        light_filter="V",
                    )
                )
            yield batch

    def __write_to_csv(self, url: str, path: Path) -> None:
        with self._http_client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_bytes(1024 * 1024):
                    f.write(chunk)
