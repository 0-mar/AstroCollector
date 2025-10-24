import csv
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

REFCAT_APASS = "apass"


class DaschIdentificatorDto(StellarObjectIdentificatorDto):
    gsc_bin_index: int
    ref_number: int


class DaschPlugin(CatalogPlugin[DaschIdentificatorDto]):
    # https://dasch.cfa.harvard.edu/dr7/web-apis/
    def __init__(self) -> None:
        super().__init__(
            "DASCH",
            "DASCH was the project to digitize the Harvard College Observatory’s Astronomical Photographic Glass Plate Collection for scientific applications. This enormous — multi-decade — undertaking was completed in 2024. Its legacy is DASCH Data Release 7, an extraordinary dataset that enables scientific study of the entire night sky on 100-year timescales.",
            "https://dasch.cfa.harvard.edu/",
            True,
        )
        self.base_url = "https://api.starglass.cfa.harvard.edu/public"
        self.querycat_endpoint = f"{self.base_url}/dasch/dr7/querycat"
        self.lightcurve_endpoint = f"{self.base_url}/dasch/dr7/lightcurve"
        self._http_client = httpx.Client()

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[DaschIdentificatorDto]]:
        query_body = {
            "dec_deg": coords.dec.deg,
            "ra_deg": coords.ra.deg,
            "radius_arcsec": radius_arcsec,
            "refcat": REFCAT_APASS,
        }
        query_resp = self._http_client.post(self.querycat_endpoint, json=query_body)
        query_resp.raise_for_status()
        query_data = query_resp.json()

        reader = csv.reader(query_data)

        header = next(reader)
        object_ra_deg_idx = header.index("ra_deg")
        object_dec_deg_idx = header.index("dec_deg")
        gsc_bin_index_idx = header.index("gsc_bin_index")
        ref_number_idx = header.index("ref_number")

        chunk: list[DaschIdentificatorDto] = []

        for row in reader:
            if len(chunk) >= self.batch_limit():
                yield chunk
                chunk = []

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

            chunk.append(
                DaschIdentificatorDto(
                    gsc_bin_index=int(identificator_gsc_bin_index),
                    ref_number=int(identificator_ref_number),
                    ra_deg=float(identificator_ra_deg),
                    dec_deg=float(identificator_dec_deg),
                    plugin_id=plugin_id,
                    name=None,
                    dist_arcsec=coords.separation(record_coords).arcsec,
                )
            )

        if chunk != []:
            yield chunk

    def get_photometric_data(
        self, identificator: DaschIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        lc_body = {
            "gsc_bin_index": identificator.gsc_bin_index,
            "ref_number": identificator.ref_number,
            "refcat": REFCAT_APASS,
        }

        with self._http_client.stream(
            "POST", self.lightcurve_endpoint, data=lc_body
        ) as resp:
            resp.raise_for_status()

            # write to CSV in chunks
            with open(csv_path, "wb") as f:
                for chunk in resp.iter_bytes(1024 * 1024):
                    f.write(chunk)

        with open(csv_path, "r") as lc_data:
            reader = csv.reader(lc_data)

            header = next(reader)
            jd_idx = header.index("date_jd")
            mag_idx = header.index("magcal_magdep")
            err_idx = header.index("magcal_magdep_rms")

            chunk: list[PhotometricDataDto] = []

            for row in reader:
                if len(chunk) >= self.batch_limit():
                    yield chunk
                    chunk = []

                jd_str = row[jd_idx]
                mag_str = row[mag_idx]
                err_str = row[err_idx]
                if jd_str == "" or mag_str == "" or err_str == "":
                    continue

                # convert HJD_UTC to BJD_TDB
                # see DASCH time format - Time column:
                # https://dasch.cfa.harvard.edu/dr7/lightcurve-columns/
                bjd = self._to_bjd_tdb(
                    float(row[jd_idx]),
                    time_format="jd",
                    time_scale="utc",
                    reference_frame="heliocentric",
                    ra_deg=identificator.ra_deg,
                    dec_deg=identificator.dec_deg,
                )

                mag = float(row[mag_idx])
                err = float(row[err_idx])

                chunk.append(
                    PhotometricDataDto(
                        julian_date=bjd,
                        magnitude=mag,
                        magnitude_error=err,
                        plugin_id=identificator.plugin_id,
                        light_filter=None,
                    )
                )

        if chunk != []:
            yield chunk
