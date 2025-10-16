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


class AsasnIdentificatorDto(StellarObjectIdentificatorDto):
    asasn_uuid: str


class AsasnPlugin(CatalogPlugin[AsasnIdentificatorDto]):
    def __init__(self) -> None:
        # the data comes from here
        # https://asas-sn.osu.edu/variables
        super().__init__()
        self._directly_identifies_objects = True
        self._description = "The sky is very big: until recently, only human eyes fully surveyed the sky for the transient, variable and violent events that are crucial probes of the nature and physics of our Universe. We changed that with our All-Sky Automated Survey for Supernovae (ASAS-SN) project, which is now automatically surveying the entire visible sky every night down to about 18th magnitude, more than 50,000 times deeper than human eye."
        self._catalog_url = "https://www.astronomy.ohio-state.edu/asassn/index.shtml"
        self._http_client = httpx.Client(timeout=10.0)
        self._base_url = "https://asas-sn.osu.edu"

    def _search_url(self, coords: SkyCoord, radius_arcsec: float) -> str:
        return f"https://asas-sn.osu.edu/variables?ra={coords.ra.deg}&dec={coords.dec.deg}&radius={radius_arcsec / 60}&vmag_min=&vmag_max=&amplitude_min=&amplitude_max=&period_min=&period_max=&lksl_min=&lksl_max=&class_prob_min=&class_prob_max=&parallax_over_err_min=&parallax_over_err_max=&name=&references[]=I&references[]=II&references[]=III&references[]=IV&references[]=V&references[]=IX&sort_by=raj2000&sort_order=asc&show_non_periodic=true&show_without_class=true&asassn_discov_only=false&"

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[AsasnIdentificatorDto]]:
        response = self._http_client.get(self._search_url(coords, radius_arcsec))
        response.raise_for_status()
        html = response.text

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", attrs={"class": "table table-striped table-hover"})
        body = table.find("tbody")

        rows = body.find_all("tr")

        chunk: list[AsasnIdentificatorDto] = []

        for row in rows:
            if len(chunk) >= self.batch_limit():
                yield chunk
                chunk = []

            row_cols = row.find_all("td")

            if len(row_cols) < 5:
                continue  # skip malformed rows

            a = row_cols[0].find("a")
            if not a:
                continue

            link = a["href"]
            asasn_uuid = link.split("/")[-1]

            name = row_cols[1].text
            ra = float(row_cols[2].text)
            dec = float(row_cols[3].text)
            dst_arc_sec = float(row_cols[4].text)

            chunk.append(
                AsasnIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=ra,
                    dec_deg=dec,
                    name=name if name != "" else None,
                    dist_arcsec=dst_arc_sec,
                    asasn_uuid=asasn_uuid,
                )
            )

        if chunk != []:
            yield chunk

    def get_photometric_data(
        self, identificator: AsasnIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        data_url = f"{self._base_url}/variables/{identificator.asasn_uuid}.json"

        resp = self._http_client.get(data_url)
        resp.raise_for_status()
        data = resp.json()

        chunk: list[PhotometricDataDto] = []
        with open(csv_path, mode="w") as csv_file:
            csv_file.write("hjd,camera,mag,mag_err,flux,flux_err\n")

            for result in data["results"]:
                csv_file.write(
                    f"{result['hjd']},{result['camera']},{result['mag']},{result['mag_err']},{result['flux']},{result['flux_err']}\n"
                )
                if len(chunk) >= self.batch_limit():
                    yield chunk
                    chunk = []

                hjd = float(result["hjd"])
                mag = float(result["mag"])
                mag_err = float(result["mag_err"])
                bjd = self._to_bjd(
                    hjd,
                    format="jd",
                    scale="utc",
                    ra_deg=identificator.ra_deg,
                    dec_deg=identificator.dec_deg,
                    is_hjd=True,
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
