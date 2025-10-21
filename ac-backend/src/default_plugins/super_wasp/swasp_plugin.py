from pathlib import Path
from typing import Iterator
from uuid import UUID

import httpx
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)
from bs4 import BeautifulSoup


class SwaspIdentificatorDto(StellarObjectIdentificatorDto):
    swasp_id: str


class SwaspPlugin(CatalogPlugin[SwaspIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "Super WASP",
            "Wide Angle Search for Planets",
            "https://wasp.cerit-sc.cz/",
            True,
        )
        self._http_client = httpx.Client(timeout=10.0)
        self._search_url = "https://wasp.cerit-sc.cz/search"
        self._data_url = "https://wasp.cerit-sc.cz/csv"

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[SwaspIdentificatorDto]]:
        params = {
            "objid": "",
            "ra": coords.ra.deg,
            "dec": coords.dec.deg,
            "radius": radius_arcsec,
            "radiusUnit": "sec",
            "magmin": "",
            "magmax": "",
            "limit": 50,
            "ptsmin": 1,
        }

        response = self._http_client.get(self._search_url, params=params)
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", attrs={"class": "basic"})
        if table is None:
            pass

        rows = table.find_all("tr")[1:]

        targets: list[SwaspIdentificatorDto] = []

        for row in rows:
            cols = row.find_all("td")

            targets.append(
                SwaspIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=float(cols[8].text),
                    dec_deg=float(cols[9].text),
                    name=cols[2].text,
                    dist_arcsec=(float(cols[11].text) * u.deg).to(u.arcsec).value,
                    swasp_id=cols[2].text,
                )
            )

        yield targets

    def get_photometric_data(
        self, identificator: SwaspIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        self.__write_to_csv(self._data_url, identificator.swasp_id, csv_path)

        # release data in chunks
        for chunk in self.__get_chunk(csv_path, identificator):
            if chunk == []:
                continue

            yield chunk

    def __write_to_csv(self, url: str, swasp_id: str, path: Path) -> None:
        with self._http_client.stream("GET", url, params={"object": swasp_id}) as resp:
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_bytes(1024 * 1024):
                    f.write(chunk)

    def __get_chunk(
        self, path: Path, identificator: SwaspIdentificatorDto
    ) -> Iterator[list[PhotometricDataDto]]:
        for chunk in pd.read_csv(
            path,
            chunksize=50_000,
            sep=",",
            engine="python",
            usecols=["HJD", "magnitude", "magnitude error"],
            dtype={
                "HJD": "float64",
                "magnitude": "float64",
                "magnitude error": "float64",
            },
            na_values=(""),
            on_bad_lines="skip",
        ):
            batch: list[PhotometricDataDto] = []
            chunk = chunk.dropna(subset=["HJD", "magnitude", "magnitude error"])
            for hjd, mag, mag_err in chunk.itertuples(index=False, name=None):
                # convert HJD_UTC to BJD_TDB
                bjd = self._to_bjd(
                    hjd,
                    format="jd",
                    scale="utc",
                    ra_deg=identificator.ra_deg,
                    dec_deg=identificator.dec_deg,
                    is_hjd=True,
                )

                batch.append(
                    PhotometricDataDto(
                        plugin_id=identificator.plugin_id,
                        julian_date=bjd,
                        magnitude=mag,
                        magnitude_error=mag_err,
                        light_filter=None,
                    )
                )
            yield batch
