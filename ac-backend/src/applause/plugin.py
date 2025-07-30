from typing import AsyncGenerator
from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy.table import Table

from fastapi.concurrency import run_in_threadpool
from pyvo.dal import AsyncTAPJob

from src.core.config.config import settings
from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)

import pyvo as vo
import requests

APPLAUSE_TAP_URL = "https://www.plate-archive.org/tap"


class ApplauseIdentificatorDto(StellarObjectIdentificatorDto):
    ucac4_id: str
    angdist: float


# TODO: what about shared session?
class ApplausePlugin(PhotometricCataloguePlugin[ApplauseIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__()
        self.__service = vo.dal.TAPService(
            APPLAUSE_TAP_URL, session=self.__tap_session()
        )

    def __tap_session(self) -> requests.Session():
        session = requests.Session()
        session.headers["Authorization"] = f"Token {settings.APPLAUSE_TOKEN}"

        return session

    def __tap_query(self, query: str, language: str) -> Table:
        # Submit job
        job = self.__service.submit_job(query, language=language, queue="1h")
        job.run()

        # Wait for result
        job.wait(phases=["COMPLETED", "ERROR", "ABORTED"])
        job.raise_if_error()

        # hack for pyvo to work
        def custom_result_uri(self):
            return f"{APPLAUSE_TAP_URL}/async/{self.job_id}/results/result"

        AsyncTAPJob.result_uri = property(custom_result_uri)

        # Fetch and print results
        results = job.fetch_result()
        job.delete()
        return results.to_table()

    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncGenerator[list[ApplauseIdentificatorDto]]:
        cone_search_query = f"""
        SELECT DISTINCT ON(ucac4_id) ucac4_id, raj2000, dej2000,
        DEGREES(SPOINT(RADIANS(raj2000), RADIANS(dej2000)) <-> SPOINT(RADIANS({coords.ra.deg}), RADIANS({coords.dec.deg}))) as angdist
        FROM applause_dr3.lightcurve
        WHERE pos @ scircle(spoint(RADIANS({coords.ra.deg}), RADIANS({coords.dec.deg})), RADIANS({radius_arcsec / 3600})) AND ucac4_id IS NOT NULL
        ORDER BY ucac4_id, angdist ASC"""

        result_table = await run_in_threadpool(
            self.__tap_query, cone_search_query, "PostgreSQL"
        )

        yield await run_in_threadpool(self.__get_object_data, plugin_id, result_table)

    def __get_object_data(
        self, plugin_id: UUID, result_table: Table
    ) -> list[ApplauseIdentificatorDto]:
        results = []
        for ucac4_id, ra, dec, angdist in result_table.iterrows(
            "ucac4_id", "raj2000", "dej2000", "angdist"
        ):
            results.append(
                ApplauseIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=ra,
                    dec_deg=dec,
                    ucac4_id=ucac4_id,
                    angdist=angdist,
                )
            )

        return results

    async def get_photometric_data(
        self, identificator: ApplauseIdentificatorDto
    ) -> AsyncGenerator[list[PhotometricDataDto]]:
        lc_query = f"""SELECT ucac4_id,jd_mid, bmag, bmagerr, vmag, vmagerr FROM applause_dr3.lightcurve
        WHERE ucac4_id='{identificator.ucac4_id}'
        ORDER BY jd_mid"""

        result_table = await run_in_threadpool(self.__tap_query, lc_query, "PostgreSQL")

        yield await run_in_threadpool(self.__get_lc_data, result_table, identificator)

    def __get_lc_data(
        self, lightcurve_table, identificator
    ) -> list[PhotometricDataDto]:
        results: list[PhotometricDataDto] = []
        for jd_mid, bmag, bmagerr in lightcurve_table.iterrows(
            "jd_mid", "bmag", "bmagerr"
        ):
            results.append(
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=jd_mid,
                    magnitude=bmag,
                    magnitude_error=bmagerr,
                    v_magnitude=None,
                    v_magnitude_error=None,
                    b_magnitude=bmag,
                    b_magnitude_error=bmagerr,
                )
            )

        return results
