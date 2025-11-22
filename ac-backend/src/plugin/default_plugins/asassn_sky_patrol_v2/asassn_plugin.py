from pathlib import Path
from typing import Iterator
from uuid import UUID

import httpx
from astropy.coordinates import SkyCoord
from astropy import units as u

from src.plugin.interface.catalog_plugin import DefaultCatalogPlugin
from src.plugin.interface.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)


class AsassnIdentificatorDto(StellarObjectIdentificatorDto):
    asas_sn_id: int


class AsassnPlugin(DefaultCatalogPlugin[AsassnIdentificatorDto]):
    def __init__(self) -> None:
        # the data comes from here
        # http://asas-sn.ifa.hawaii.edu/skypatrol/
        super().__init__(
            "ASAS-SN Sky Patrol",
            "The sky is very big: until recently, only human eyes fully surveyed the sky for the transient, variable and violent events that are crucial probes of the nature and physics of our Universe. We changed that with our All-Sky Automated Survey for Supernovae (ASAS-SN) project, which is now automatically surveying the entire visible sky every night down to about 18th magnitude, more than 50,000 times deeper than human eye.",
            "https://www.astronomy.ohio-state.edu/asassn/index.shtml",
            True,
        )
        self._http_client = httpx.Client(timeout=10.0)

    def _search_url(self, coords: SkyCoord, radius_arcsec: float) -> str:
        return f"http://asassn-lb01.ifa.hawaii.edu:9006/lookup_cone/radius{radius_arcsec / 3600}_ra{coords.ra.deg}_dec{coords.dec.deg}"

    def _data_url(self, asas_sn_id: int) -> str:
        return f"http://asassn-lb01.ifa.hawaii.edu:9006/get_lightcurve/{asas_sn_id}"

    def list_objects(
        self,
        coords: SkyCoord,
        radius_arcsec: float,
        plugin_id: UUID,
        resources_dir: Path,
    ) -> Iterator[list[AsassnIdentificatorDto]]:
        request_body = {
            "catalog": "master_list",
            "cols": ["asas_sn_id", "catalog_sources", "ra_deg", "dec_deg"],
            "format": "json",
            "n_rows": 1000,
            "page_num": 0,
        }

        response = self._http_client.post(
            self._search_url(coords, radius_arcsec), json=request_body
        )
        response.raise_for_status()
        data = response.json()

        chunk: list[AsassnIdentificatorDto] = []

        for record in data["data"]:
            if len(chunk) >= self.batch_limit():
                yield chunk
                chunk = []

            asas_sn_id = record["asas_sn_id"]
            ra_deg = float(record["ra_deg"])
            dec_deg = float(record["dec_deg"])

            target = SkyCoord(ra=ra_deg, dec=dec_deg, unit=u.deg)

            chunk.append(
                AsassnIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=ra_deg,
                    dec_deg=dec_deg,
                    name=None,
                    dist_arcsec=coords.separation(target).arcsec,
                    asas_sn_id=asas_sn_id,
                )
            )

        if chunk != []:
            yield chunk

    def get_photometric_data(
        self, identificator: AsassnIdentificatorDto, csv_path: Path, resources_dir: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        response = self._http_client.get(self._data_url(identificator.asas_sn_id))
        response.raise_for_status()
        data_json = response.json()

        chunk: list[PhotometricDataDto] = []

        with open(csv_path, mode="w") as csv_file:
            csv_file.write(
                "hjd,flux,flux_err,mag,mag_err,limit,fwhm,image_id,quality\n"
            )

            for record in data_json["light_curve"]["data"]:
                csv_file.write(
                    f"{record[0]},{record[1]},{record[2]},{record[3]},{record[4]},{record[5]},{record[6]},{record[7]},{record[8]}\n"
                )

                if len(chunk) >= self.batch_limit():
                    yield chunk
                    chunk = []

                hjd = record[0]
                mag = record[3]
                mag_err = record[4]

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
                        magnitude=mag,
                        magnitude_error=mag_err,
                        plugin_id=identificator.plugin_id,
                        light_filter="V",
                    )
                )

        if chunk != []:
            yield chunk
