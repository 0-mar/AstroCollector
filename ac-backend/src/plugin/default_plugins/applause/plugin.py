from pathlib import Path
from typing import Iterator
from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy.table import Table

from pyvo.dal import AsyncTAPJob

from src.core.config.config import settings
from src.plugin.interface.catalog_plugin import DefaultCatalogPlugin
from src.plugin.interface.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)

import pyvo as vo
import requests

APPLAUSE_TAP_URL = "https://www.plate-archive.org/tap"


class ApplauseIdentificatorDto(StellarObjectIdentificatorDto):
    ucac4_id: str


class ApplausePlugin(DefaultCatalogPlugin[ApplauseIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "APPLAUSE",
            "German astronomical observatories own considerable collection of photographic plates. While these observations lead to significant discoveries in the past, they are also of interest for scientists today and in the future. In particular, for the study of long-term variability of many types of stars, these measurements are of immense scientific value.",
            "https://www.plate-archive.org/cms/home/",
            True,
        )
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

    def list_objects(
        self,
        coords: SkyCoord,
        radius_arcsec: float,
        plugin_id: UUID,
        resources_dir: Path,
    ) -> Iterator[list[ApplauseIdentificatorDto]]:
        cone_search_query = f"""
        SELECT DISTINCT ON(ucac4_id) ucac4_id, raj2000, dej2000,
        3600.0 * DEGREES(SPOINT(RADIANS(raj2000), RADIANS(dej2000)) <-> SPOINT(RADIANS({coords.ra.deg}), RADIANS({coords.dec.deg}))) as angdist_arcsec
        FROM applause_dr3.lightcurve
        WHERE pos @ scircle(spoint(RADIANS({coords.ra.deg}), RADIANS({coords.dec.deg})), RADIANS({radius_arcsec / 3600.0})) AND ucac4_id IS NOT NULL
        ORDER BY ucac4_id, angdist_arcsec ASC"""

        result_table = self.__tap_query(cone_search_query, "PostgreSQL")

        chunk = []
        # TODO: how do I get the name?
        for ucac4_id, ra, dec, angdist_arcsec in result_table.iterrows(
            "ucac4_id", "raj2000", "dej2000", "angdist_arcsec"
        ):
            if len(chunk) >= self.batch_limit():
                yield chunk
                chunk = []

            chunk.append(
                ApplauseIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=ra,
                    dec_deg=dec,
                    ucac4_id=ucac4_id,
                    name=None,
                    dist_arcsec=angdist_arcsec,
                )
            )

        if chunk != []:
            yield chunk

    def __get_object_data(
        self, plugin_id: UUID, result_table: Table
    ) -> list[ApplauseIdentificatorDto]:
        results = []
        # TODO: how do I get the name?
        for ucac4_id, ra, dec, angdist_arcsec in result_table.iterrows(
            "ucac4_id", "raj2000", "dej2000", "angdist_arcsec"
        ):
            results.append(
                ApplauseIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=ra,
                    dec_deg=dec,
                    ucac4_id=ucac4_id,
                    name=None,
                    dist_arcsec=angdist_arcsec,
                )
            )

        return results

    def get_photometric_data(
        self,
        identificator: ApplauseIdentificatorDto,
        csv_path: Path,
        resources_dir: Path,
    ) -> Iterator[list[PhotometricDataDto]]:
        lc_query = f"""SELECT ucac4_id, jd_mid, bmag, bmagerr, vmag, vmagerr FROM applause_dr3.lightcurve
        WHERE ucac4_id='{identificator.ucac4_id}' ORDER BY jd_mid"""

        result_table = self.__tap_query(lc_query, "PostgreSQL")
        result_table.write(csv_path)

        chunk: list[PhotometricDataDto] = []
        for jd_mid, bmag, bmagerr, vmag, vmagerr in result_table.iterrows(
            "jd_mid ", "bmag", "bmagerr", "vmag", "vmagerr"
        ):
            if len(chunk) >= self.batch_limit():
                yield chunk
                chunk = []

            # convert JD_UTC to BJD_TDB
            bjd = self._to_bjd_tdb(
                jd_mid,
                time_format="jd",
                time_scale="utc",
                reference_frame="geocentric",
                ra_deg=identificator.ra_deg,
                dec_deg=identificator.dec_deg,
            )

            chunk.append(
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=bjd,
                    magnitude=bmag,
                    magnitude_error=bmagerr,
                    light_filter="B",
                )
            )

            chunk.append(
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=bjd,
                    magnitude=vmag,
                    magnitude_error=vmagerr,
                    light_filter="V",
                )
            )

        if chunk != []:
            yield chunk
