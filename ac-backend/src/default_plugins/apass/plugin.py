from pathlib import Path
from typing import Iterator
from uuid import UUID

import httpx
from astropy.coordinates import SkyCoord

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)
from bs4 import BeautifulSoup


class ApassIdentificatorDto(StellarObjectIdentificatorDto):
    raddeg: float


class ApassPlugin(CatalogPlugin[ApassIdentificatorDto]):
    # https://tombstone.physics.mcmaster.ca/APASS/conesearch_offset.php
    def __init__(self) -> None:
        super().__init__(
            "APASS",
            "Through a grant from the Robert Martin Ayers Sciences Fund, the AAVSO is performing an all-sky photometric survey. This survey is conducted in eight filters: Johnson B and V, plus Sloan u', g′, r′, i′, z_s and Z. It is valid from about 7th magnitude to about 17th magnitude. Precise, reliable standardized photometry in this magnitude range is in high demand, both from our observers and from the professional community.",
            "https://www.aavso.org/apass",
            False,
        )
        self._url = "https://tombstone.physics.mcmaster.ca/APASS/conesearch_offset.php"
        self._http_client = httpx.Client(timeout=10.0)

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[ApassIdentificatorDto]]:
        query_params = {
            "radeg": f"{coords.ra.deg}",
            "decdeg": f"{coords.dec.deg}",
            "raddeg": f"{radius_arcsec / 3600}",
        }
        query_resp = self._http_client.get(self._url, params=query_params)
        html = query_resp.text

        soup = BeautifulSoup(html, "html.parser")
        root = soup.find("font", attrs={"face": "courier"})
        if root.text == "No rows were returned by query.":
            return

        # TODO: how do I resolve names & distances?
        else:
            yield [
                ApassIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=coords.ra.deg,
                    dec_deg=coords.dec.deg,
                    raddeg=radius_arcsec / 3600,
                    name=None,
                    dist_arcsec=0,
                )
            ]

    def get_photometric_data(
        self, identificator: ApassIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        query_params = {
            "radeg": f"{identificator.ra_deg}",
            "decdeg": f"{identificator.dec_deg}",
            "raddeg": f"{identificator.raddeg}",
        }
        query_resp = self._http_client.get(self._url, params=query_params)
        html = query_resp.text

        chunk: list[PhotometricDataDto] = []

        soup = BeautifulSoup(html, "html.parser")
        root = soup.find("font", attrs={"face": "courier"})
        records = root.get_text(strip=True, separator="\n").splitlines()

        if records[0] == "No rows were returned by query.":
            return

        with open(csv_path, mode="w") as csv_file:
            csv_file.write(records[1] + "\n")

            for i in range(2, len(records)):
                if len(chunk) >= self.batch_limit():
                    yield chunk
                    chunk = []

                record = records[i]

                csv_file.write(record + "\n")

                # hjd-24e5, mag, errmag, filter
                values = record.split(",")

                # convert HJD_UTC to BJD_TDB
                hjd = float(values[0]) + 2400000
                bjd = self._to_bjd_tdb(
                    hjd,
                    time_format="jd",
                    time_scale="utc",
                    reference_frame="heliocentric",
                    ra_deg=identificator.ra_deg,
                    dec_deg=identificator.dec_deg,
                )

                chunk.append(
                    PhotometricDataDto(
                        julian_date=bjd,
                        magnitude=float(values[1]),
                        magnitude_error=float(values[2]),
                        plugin_id=identificator.plugin_id,
                        light_filter=values[3].strip("'"),
                    )
                )

        if chunk != []:
            yield chunk
