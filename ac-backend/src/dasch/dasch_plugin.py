import csv
from typing import List
from uuid import UUID

from fastapi.concurrency import run_in_threadpool

from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import PhotometricDataDto
from src.dasch.dasch_identificator_model import DaschStellarObjectIdentificatorDto

REFCAT_APASS = "apass"


class DaschPlugin(PhotometricCataloguePlugin[DaschStellarObjectIdentificatorDto]):
    # https://dasch.cfa.harvard.edu/dr7/web-apis/
    def __init__(self) -> None:
        super().__init__()
        self.base_url = "https://api.starglass.cfa.harvard.edu/public"
        self.querycat_endpoint = f"{self.base_url}/dasch/dr7/querycat"
        self.lightcurve_endpoint = f"{self.base_url}/dasch/dr7/lightcurve"

    async def list_objects(
        self, ra_deg: float, dec_deg: float, radius_arcsec: float, plugin_id: UUID
    ) -> List[DaschStellarObjectIdentificatorDto]:
        query_body = {
            "dec_deg": dec_deg,
            "ra_deg": ra_deg,
            "radius_arcsec": radius_arcsec,
            "refcat": REFCAT_APASS,
        }
        async with self._http_client.post(
            self.querycat_endpoint, json=query_body
        ) as query_resp:
            query_data = await query_resp.json()

        reader = await run_in_threadpool(csv.reader, query_data)

        header = next(reader)
        object_ra_deg_idx = header.index("ra_deg")
        object_dec_deg_idx = header.index("dec_deg")
        gsc_bin_index_idx = header.index("gsc_bin_index")
        ref_number_idx = header.index("ref_number")

        return await run_in_threadpool(
            self._process_objects_csv,
            reader,
            object_ra_deg_idx,
            object_dec_deg_idx,
            gsc_bin_index_idx,
            ref_number_idx,
            plugin_id,
        )

    def _process_objects_csv(
        self,
        reader,
        object_ra_deg_idx,
        object_dec_deg_idx,
        gsc_bin_index_idx,
        ref_number_idx,
        plugin_id: UUID,
    ) -> list[DaschStellarObjectIdentificatorDto]:
        result = []
        for row in reader:
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

            result.append(
                DaschStellarObjectIdentificatorDto(
                    gsc_bin_index=int(identificator_gsc_bin_index),
                    ref_number=int(identificator_ref_number),
                    ra_deg=float(identificator_ra_deg),
                    dec_deg=float(identificator_dec_deg),
                    plugin_id=plugin_id,
                )
            )

        return result

        # sess = daschlab.open_session()
        # sess.select_target(ra_deg, dec_deg).select_refcat("apass")
        # curve = sess.lightcurve()
        # closest_object

    async def get_photometric_data(
        self, identificator: DaschStellarObjectIdentificatorDto
    ) -> List[PhotometricDataDto]:
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

        return await run_in_threadpool(
            self._process_photometric_data_csv,
            reader,
            jd_idx,
            mag_idx,
            err_idx,
            identificator.plugin_id,
        )

    def _process_photometric_data_csv(
        self, reader, jd_idx, mag_idx, err_idx, plugin_id: UUID
    ) -> List[PhotometricDataDto]:
        result = []
        for row in reader:
            jd_str = row[jd_idx]
            mag_str = row[mag_idx]
            err_str = row[err_idx]
            if jd_str == "" or mag_str == "" or err_str == "":
                continue

            jd = float(row[jd_idx])
            mag = float(row[mag_idx])
            err = float(row[err_idx])

            result.append(
                PhotometricDataDto(
                    julian_date=jd, magnitude=mag, error=err, plugin_id=plugin_id
                )
            )

        return result
