from typing import List, AsyncIterator, Any
from uuid import UUID

from astropy.coordinates import SkyCoord
from fastapi.concurrency import run_in_threadpool

from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)


class Mmt9IdentificatorDto(StellarObjectIdentificatorDto):
    radius_arcsec: float


class Mmt9Plugin(PhotometricCataloguePlugin[Mmt9IdentificatorDto]):
    # http://survey.favor2.info/favor2/
    def __init__(self) -> None:
        super().__init__()
        self._url = "http://survey.favor2.info/favor2/photometry/json"

    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncIterator[List[Mmt9IdentificatorDto]]:
        query_params = {
            "coords": f"{coords.ra.deg} {coords.dec.deg} ",
            "sr": f"{radius_arcsec / 3600}",
            "sr_value": f"f{radius_arcsec}",
            "sr_units": "arcsec",
            "name": "degrees",
            "ra": f"{coords.ra.deg}",
            "dec": f"{coords.dec.deg}",
        }
        async with self._http_client.get(self._url, params=query_params) as query_resp:
            query_data = await query_resp.json()

        if query_data["lcs"] == []:
            yield []

        yield [
            Mmt9IdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=coords.ra.deg,
                dec_deg=coords.dec.deg,
                radius_arcsec=radius_arcsec,
            )
        ]

    async def get_photometric_data(
        self, identificator: Mmt9IdentificatorDto
    ) -> AsyncIterator[List[Mmt9IdentificatorDto]]:
        query_params = {
            "coords": f"{identificator.ra_deg} {identificator.dec_deg} ",
            "sr": f"{identificator.radius_arcsec / 3600}",
            "sr_value": f"f{identificator.radius_arcsec}",
            "sr_units": "arcsec",
            "name": "degrees",
            "ra": f"{identificator.ra_deg}",
            "dec": f"{identificator.dec_deg}",
        }
        async with self._http_client.get(self._url, params=query_params) as query_resp:
            query_data = await query_resp.json()

        yield await run_in_threadpool(
            self._process_photometric_data_batch,
            query_data,
            identificator,
        )

    def _process_photometric_data_batch(
        self, data: Any, identificator: Mmt9IdentificatorDto
    ) -> List[PhotometricDataDto]:
        result: list[PhotometricDataDto] = []

        for record in data["lcs"]:
            for i in range(len(record["mags"])):
                # convert MJD_UTC to BJD_TDB
                bjd = self._to_bjd(
                    float(record["mjds"][i]),
                    format="mjd",
                    scale="utc",
                    ra_deg=identificator.ra_deg,
                    dec_deg=identificator.dec_deg,
                    is_hjd=False,
                )

                result.append(
                    PhotometricDataDto(
                        julian_date=bjd,
                        magnitude=record["mags"][i],
                        magnitude_error=record["magerrs"][i],
                        plugin_id=identificator.plugin_id,
                        light_filter=record["filter"],
                    )
                )

        return result
