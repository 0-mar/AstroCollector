from typing import List, AsyncIterator
from uuid import UUID

from astropy.coordinates import SkyCoord
from fastapi.concurrency import run_in_threadpool

from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)
from bs4 import BeautifulSoup


class ApassIdentificatorDto(StellarObjectIdentificatorDto):
    raddeg: float


class ApassPlugin(PhotometricCataloguePlugin[ApassIdentificatorDto]):
    # https://tombstone.physics.mcmaster.ca/APASS/conesearch_offset.php
    def __init__(self) -> None:
        super().__init__()
        self._url = "https://tombstone.physics.mcmaster.ca/APASS/conesearch_offset.php"

    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncIterator[List[ApassIdentificatorDto]]:
        query_params = {
            "radeg": f"{coords.ra.deg}",
            "decdeg": f"{coords.dec.deg}",
            "raddeg": f"{radius_arcsec / 3600}",
        }
        async with self._http_client.get(self._url, params=query_params) as query_resp:
            html = await query_resp.text()

        soup = BeautifulSoup(html, "html.parser")
        root = soup.find("font", attrs={"face": "courier"})
        if root.text == "No rows were returned by query.":
            yield []

        else:
            yield [
                ApassIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=coords.ra.deg,
                    dec_deg=coords.dec.deg,
                    raddeg=radius_arcsec / 3600,
                )
            ]

    async def get_photometric_data(
        self, identificator: ApassIdentificatorDto
    ) -> AsyncIterator[List[ApassIdentificatorDto]]:
        query_params = {
            "radeg": f"{identificator.ra_deg}",
            "decdeg": f"{identificator.dec_deg}",
            "raddeg": f"{identificator.raddeg}",
        }
        async with self._http_client.get(self._url, params=query_params) as query_resp:
            html = await query_resp.text()

        batch = await run_in_threadpool(
            self._process_photometric_data_batch,
            html,
            identificator.plugin_id,
        )

        if batch == []:
            return

        yield batch

    def _process_photometric_data_batch(
        self, html: str, plugin_id: UUID
    ) -> List[PhotometricDataDto]:
        result: list[PhotometricDataDto] = []

        soup = BeautifulSoup(html, "html.parser")
        root = soup.find("font", attrs={"face": "courier"})
        records = root.get_text(strip=True, separator="\n").splitlines()

        if records[0] == "No rows were returned by query.":
            return []

        for i in range(2, len(records)):
            record = records[i]

            # hjd-24e5, mag, errmag, filter
            values = record.split(",")
            result.append(
                PhotometricDataDto(
                    julian_date=float(values[0])
                    + 2400000,  # hjd-24e5 = HJD - 2 400 000
                    magnitude=float(values[1]),
                    magnitude_error=float(values[2]),
                    plugin_id=plugin_id,
                    light_filter=values[3].strip("'"),
                )
            )

        return result
