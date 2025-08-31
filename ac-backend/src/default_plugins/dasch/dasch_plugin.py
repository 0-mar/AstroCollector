import csv
from typing import List, Iterator, AsyncIterator
from uuid import UUID

from astropy.coordinates import SkyCoord
from fastapi.concurrency import run_in_threadpool

from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)


REFCAT_APASS = "apass"


class DaschStellarObjectIdentificatorDto(StellarObjectIdentificatorDto):
    gsc_bin_index: int
    ref_number: int


class DaschPlugin(PhotometricCataloguePlugin[DaschStellarObjectIdentificatorDto]):
    # https://dasch.cfa.harvard.edu/dr7/web-apis/
    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://api.starglass.cfa.harvard.edu/public"
        self.querycat_endpoint = f"{self.base_url}/dasch/dr7/querycat"
        self.lightcurve_endpoint = f"{self.base_url}/dasch/dr7/lightcurve"

    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncIterator[List[DaschStellarObjectIdentificatorDto]]:
        query_body = {
            "dec_deg": coords.dec.deg,
            "ra_deg": coords.ra.deg,
            "radius_arcsec": radius_arcsec,
            "refcat": REFCAT_APASS,
        }
        async with self._http_client.post(
            self.querycat_endpoint, json=query_body
        ) as query_resp:
            query_data = await query_resp.json()

        # for blocking tasks, run in external threadpool
        reader = await run_in_threadpool(csv.reader, query_data)

        header = next(reader)
        object_ra_deg_idx = header.index("ra_deg")
        object_dec_deg_idx = header.index("dec_deg")
        gsc_bin_index_idx = header.index("gsc_bin_index")
        ref_number_idx = header.index("ref_number")

        # yield processed data chunks
        while True:
            batch = await run_in_threadpool(
                self._process_objects_batch,
                reader,
                object_ra_deg_idx,
                object_dec_deg_idx,
                gsc_bin_index_idx,
                ref_number_idx,
                plugin_id,
                coords,
            )

            if batch == []:
                # Signals end of iterator
                return

            yield batch

    def _process_objects_batch(
        self,
        reader: Iterator[list[str]],
        object_ra_deg_idx: int,
        object_dec_deg_idx: int,
        gsc_bin_index_idx: int,
        ref_number_idx: int,
        plugin_id: UUID,
        search_coords: SkyCoord,
    ) -> list[DaschStellarObjectIdentificatorDto]:
        result: list[DaschStellarObjectIdentificatorDto] = []

        for row in reader:
            if len(result) >= self.batch_limit():
                break

            identificator_ra_deg = row[object_ra_deg_idx]
            identificator_dec_deg = row[object_dec_deg_idx]
            identificator_gsc_bin_index = row[gsc_bin_index_idx]
            identificator_ref_number = row[ref_number_idx]
            if (
                identificator_ra_deg == ""
                or identificator_dec_deg == ""
                or identificator_gsc_bin_index == ""
                or identificator_ref_number == ""
            ):
                continue

            record_coords = SkyCoord(
                identificator_ra_deg, identificator_dec_deg, unit="deg"
            )

            result.append(
                DaschStellarObjectIdentificatorDto(
                    gsc_bin_index=int(identificator_gsc_bin_index),
                    ref_number=int(identificator_ref_number),
                    ra_deg=float(identificator_ra_deg),
                    dec_deg=float(identificator_dec_deg),
                    plugin_id=plugin_id,
                    name="",
                    dist_arcsec=search_coords.separation(record_coords).arcsec,
                )
            )

        return result

        # sess = daschlab.open_session()
        # sess.select_target(ra_deg, dec_deg).select_refcat("apass")
        # curve = sess.lightcurve()
        # closest_object

    async def get_photometric_data(
        self, identificator: DaschStellarObjectIdentificatorDto
    ) -> AsyncIterator[List[PhotometricDataDto]]:
        lc_body = {
            "gsc_bin_index": identificator.gsc_bin_index,
            "ref_number": identificator.ref_number,
            "refcat": REFCAT_APASS,
        }

        async with self._http_client.post(
            self.lightcurve_endpoint, json=lc_body
        ) as lc_resp:
            lc_data = await lc_resp.json()

        reader = await run_in_threadpool(csv.reader, lc_data)

        header = next(reader)
        jd_idx = header.index("date_jd")
        mag_idx = header.index("magcal_magdep")
        err_idx = header.index("magcal_magdep_rms")

        while True:
            batch = await run_in_threadpool(
                self._process_photometric_data_batch,
                reader,
                jd_idx,
                mag_idx,
                err_idx,
                identificator,
            )

            if batch == []:
                return

            yield batch

    def _process_photometric_data_batch(
        self,
        reader: Iterator[list[str]],
        jd_idx: int,
        mag_idx: int,
        err_idx: int,
        identificator: DaschStellarObjectIdentificatorDto,
    ) -> List[PhotometricDataDto]:
        result: list[PhotometricDataDto] = []
        for row in reader:
            if len(result) >= self.batch_limit():
                break
            jd_str = row[jd_idx]
            mag_str = row[mag_idx]
            err_str = row[err_idx]
            if jd_str == "" or mag_str == "" or err_str == "":
                continue

            # convert HJD_UTC to BJD_TDB
            # see DASCH time format - Time column:
            # https://dasch.cfa.harvard.edu/dr7/lightcurve-columns/
            bjd = self._to_bjd(
                float(row[jd_idx]),
                format="jd",
                scale="utc",
                ra_deg=identificator.ra_deg,
                dec_deg=identificator.dec_deg,
                is_hjd=True,
            )

            mag = float(row[mag_idx])
            err = float(row[err_idx])

            result.append(
                PhotometricDataDto(
                    julian_date=bjd,
                    magnitude=mag,
                    magnitude_error=err,
                    plugin_id=identificator.plugin_id,
                    light_filter=None,
                )
            )

        return result
