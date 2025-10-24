from pathlib import Path
from typing import Iterator
from uuid import UUID

import httpx
from astropy.coordinates import SkyCoord
from astropy import units as u

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)
from bs4 import BeautifulSoup


class AsasIdentificatorDto(StellarObjectIdentificatorDto):
    asas_id: str


class AsasPlugin(CatalogPlugin[AsasIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "ASAS",
            "The All Sky Automated Survey (ASAS) is a low cost project dedicated to constant photometric monitoring of the whole available sky, which is approximately 10^7 stars brighter than 14 magnitude. The project's ultimate goal is detection and investigation of of any kind of the photometric variability. One of the main objectives of ASAS is to find and catalog variable stars.",
            "https://www.astrouw.edu.pl/asas/?page=main",
            True,
        )
        self._http_client = httpx.Client(timeout=10.0)
        self._search_url = "https://www.astrouw.edu.pl/cgi-asas/asas_cat_input"

    def _data_url(self, asas_id: str) -> str:
        return f"https://www.astrouw.edu.pl/cgi-asas/asas_cgi_get_data?{asas_id},asas3"

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[AsasIdentificatorDto]]:
        # valid identifiers are in format:
        # RA[h] DEC[deg]
        # see https://www.astrouw.edu.pl/asas/i_aasc/aasc_form.php?catsrc=asas3
        ra_h = coords.ra.to(u.hourangle).value
        dec_deg = coords.dec.to(u.deg).value
        search_coords = f"{ra_h} {dec_deg}"

        form_data = {
            "source": "asas3",
            "coo": search_coords,
            "equinox": "2000",
            "nmin": "4",
            "box": str(radius_arcsec),
            "submit": "Search",
        }

        resp = self._http_client.post(self._search_url, data=form_data)
        resp.raise_for_status()
        html = resp.text

        # POLIVKAAA
        soup = BeautifulSoup(html, "html.parser")
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        records = soup.find("pre").find("pre")
        lines = records.get_text("\n").strip().split("\n\n")
        if lines[0].startswith("Not found"):
            return

        unique_ids: set[str] = set()

        # sometimes there are duplicate IDs
        for line in lines:
            asas_id, _ = line.split("\n")
            unique_ids.add(asas_id)

        targets: list[AsasIdentificatorDto] = []
        for asas_id in unique_ids:
            # ASAS ID is coded from the star's RA_2000 and DEC_2000 in the format: hhmmss+ddmm.m
            target_coords = self._asas_id_to_coord(asas_id)
            targets.append(
                AsasIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=target_coords.ra.deg,
                    dec_deg=target_coords.dec.deg,
                    name=None,
                    dist_arcsec=coords.separation(target_coords).arcsec,
                    asas_id=asas_id,
                )
            )

        yield targets

    def get_photometric_data(
        self, identificator: AsasIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        resp = self._http_client.get(self._data_url(identificator.asas_id))
        resp.raise_for_status()
        html = resp.text

        lines = html.split("\n")

        chunk: list[PhotometricDataDto] = []
        # Each data row consists of the following fields:
        # -  HJD-2450000
        # -  magnitudes (one for each aperture)
        # -  frame errors describing average photometric quality of the frame (for each aperture)
        # -  frame number
        # -  grade :
        #    A - best data, no 29.999 (not measured) indication
        #    B - mean data, no 29.999 (not measured) indication
        #    C - A and B with 29.999 (not measured) indication
        #    D - worst data, probably useless

        # the data is in format:
        # HJD      MAG_0  MAG_1  MAG_2  MAG_3  MAG_4    MER_0 MER_1 MER_2 MER_3 MER_4 GRADE FRAME
        # skip C and D grade data

        # determine the selected column based on smallest average magnitude error
        mag_errors = [0, 0, 0, 0]
        count = 0
        for line in lines:
            if line.startswith("#") or line == "":
                continue
            stripped = line.strip()
            tokens = stripped.split()
            if tokens[11] == "C" or tokens[11] == "D":
                continue

            count += 1
            magnitude_errors = list(map(float, tokens[6:11]))
            mag_errors[0] += magnitude_errors[0]
            mag_errors[1] += magnitude_errors[1]
            mag_errors[2] += magnitude_errors[2]
            mag_errors[3] += magnitude_errors[3]

        avgs = list(map(lambda x: x / count, mag_errors))
        smallest_mag_err = avgs[0]
        smallest_mag_err_idx = 0
        for i in range(len(avgs)):
            if avgs[i] < smallest_mag_err:
                smallest_mag_err_idx = i
                smallest_mag_err = avgs[i]

        # process data
        with open(csv_path, mode="w") as csv_file:
            csv_file.write(
                "HJD MAG_0,MAG_1,MAG_2,MAG_3,MAG_4,MER_0,MER_1,MER_2,MER_3,MER_4,GRADE,FRAME\n"
            )

            for line in lines:
                if len(chunk) >= self.batch_limit():
                    yield chunk
                    chunk = []

                if line.startswith("#") or line == "":
                    continue

                stripped = line.strip()
                csv_file.write(stripped + "\n")

                tokens = stripped.split()
                if tokens[11] == "C" or tokens[11] == "D":
                    continue

                mag, mag_err = (
                    float(tokens[1 + smallest_mag_err_idx]),
                    float(tokens[6 + smallest_mag_err_idx]),
                )
                hjd = float(tokens[0]) + 2450000

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

    # ASAS-ID - ASAS identification (coded from the star's RA_2000 and DEC_2000 in the format: hhmmss+ddmm.m)
    # (see https://www.astrouw.edu.pl/asas/?page=catalogues)
    # ASAS id example: 061058-2012.8
    def _asas_id_to_coord(self, asas_id: str) -> SkyCoord:
        s = asas_id.strip()
        if s.startswith("J"):
            s = s[1:]

        # split by '+' or '-'
        if "+" in s:
            ra_part, dec_part = s.split("+", 1)
            sign = +1
        elif "-" in s:
            ra_part, dec_part = s.split("-", 1)
            sign = -1
        else:
            raise ValueError("ASAS ID must contain '+' or '-' between RA and Dec")

        # RA_2000 = hhmmss  -> degrees = (hh + mm/60 + ss/3600)
        if len(ra_part) != 6:
            raise ValueError("RA part must be exactly 6 digits: hhmmss")
        hh = int(ra_part[0:2])
        mm = int(ra_part[2:4])
        ss = int(ra_part[4:6])
        ra_deg = hh + mm / 60.0 + ss / 3600.0

        # DEC_2000 = ddmm.m  -> degrees = sign * (dd + minutes/60)
        if len(dec_part) < 4:
            raise ValueError("Dec part must look like ddmm or ddmm.m")
        dd = int(dec_part[0:2])
        minutes = float(dec_part[2:])  # handles mm or mm.m
        dec_deg = sign * (dd + minutes / 60.0)

        return SkyCoord(ra=ra_deg * u.hourangle, dec=dec_deg * u.deg, frame="icrs")
