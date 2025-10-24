import logging
import math
from pathlib import Path
from typing import Iterator
from uuid import UUID

from astropy.coordinates import SkyCoord


from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)

import pyvo as vo
import requests


class GaiaDR3IdentificatorDto(StellarObjectIdentificatorDto):
    source_id: str


class GaiaDR3Plugin(CatalogPlugin[GaiaDR3IdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "Gaia DR3",
            "Launched in December 2013, Gaia is destined to create the most accurate map yet of the Milky Way. By making accurate measurements of the positions and motions of stars in the Milky Way, it will answer questions about the origin and evolution of our home galaxy.",
            "https://gaia.aip.de/",
            True,
        )
        self._tap_url = "https://gaia.aip.de/tap"
        self._tap_service = vo.dal.TAPService(
            self._tap_url, session=self.__tap_session()
        )

    def __tap_session(self) -> requests.Session():
        session = requests.Session()
        # session.headers["Authorization"] = f"Token {settings.APPLAUSE_TOKEN}"

        return session

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[GaiaDR3IdentificatorDto]]:
        lang = "ADQL"
        query = f"""
                SELECT g.source_id, g.ra, g.dec
                FROM gaiadr3.gaia_source AS g
                         JOIN gaiadr3.epoch_photometry AS ep
                              ON ep.source_id = g.source_id
                WHERE 1 = CONTAINS(
                        POINT('ICRS', g.ra, g.dec),
                        CIRCLE('ICRS', {coords.ra.deg}, {coords.dec.deg}, {radius_arcsec / 3600})
                        )
                """

        tap_result = self._tap_service.run_sync(query, language=lang)
        result_table = tap_result.to_table()

        chunk: list[GaiaDR3IdentificatorDto] = []
        for source_id, ra, dec in result_table.iterrows("source_id", "ra", "dec"):
            if len(chunk) > self.batch_limit():
                yield chunk
                chunk = []

            target = SkyCoord(ra=ra, dec=dec, unit="deg")
            dist_arcsec = coords.separation(target).arcsec

            chunk.append(
                GaiaDR3IdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=ra,
                    dec_deg=dec,
                    source_id=str(source_id),
                    name=str(source_id),
                    dist_arcsec=dist_arcsec,
                )
            )

        if chunk != []:
            yield chunk

    def get_photometric_data(
        self, identificator: GaiaDR3IdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        # for DB columns, see:
        # https://gaia.aip.de/metadata/gaiadr3/epoch_photometry/
        # https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_photometry/ssec_dm_epoch_photometry.html

        lang = "ADQL"
        lightcurve_query = f"""
         SELECT *
         from gaiadr3.epoch_photometry as lightcurves
         WHERE lightcurves.source_id = {identificator.source_id}
         """
        logging.info(identificator.source_id)
        logging.info(lightcurve_query)

        tap_result = self._tap_service.run_sync(lightcurve_query, language=lang)
        result_table = tap_result.to_table()

        # no records found in the table.
        # the table should contain only 1 row, as the times and mags are stored in an array
        if len(result_table) == 0:
            return

        # The reference epoch for time are (BJD) 2010-01-01T00:00:00.
        # Values are BJD_TCB timestamps
        g_transit_times = result_table["g_transit_time"][0].compressed()
        logging.info(len(g_transit_times))

        # G magnitudes
        g_transit_mags = result_table["g_transit_mag"][0].compressed()

        # Transit averaged G band flux
        g_transit_fluxes = result_table["g_transit_flux"][0].compressed()

        # transit averaged G band flux error
        g_transit_flux_error = result_table["g_transit_flux_error"][0].compressed()

        result_table.write(
            csv_path, fast_writer=False, format="ascii.csv", overwrite=True
        )

        chunk: list[PhotometricDataDto] = []
        for i in range(len(g_transit_times)):
            if len(chunk) >= self.batch_limit():
                yield chunk
                chunk = []

            # 2010-01-01T00:00:00 (UTC) == 2455197.5 (JD)
            bjd_tcb = g_transit_times[i] + 2455197.5
            gmag = g_transit_mags[i]
            # TODO convert to magnitude error?
            gmagerr = (2.5 / math.log(10)) * (
                g_transit_flux_error[i] / g_transit_fluxes[i]
            )

            # convert BJD_TCB to BJD_TDB
            bjd = self._to_bjd_tdb(
                bjd_tcb,
                time_format="jd",
                time_scale="tcb",
                reference_frame="barycentric",
                ra_deg=identificator.ra_deg,
                dec_deg=identificator.dec_deg,
            )

            chunk.append(
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=bjd,
                    magnitude=gmag,
                    magnitude_error=gmagerr,
                    light_filter="G",
                )
            )

        if chunk != []:
            yield chunk
