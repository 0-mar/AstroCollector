from pathlib import Path
from typing import Iterator
from uuid import UUID

import httpx
from astropy.coordinates import SkyCoord
from astropy import units as u
from astroquery.vizier import Vizier

from src.plugin.interface.catalog_plugin import DefaultCatalogPlugin
from src.plugin.interface.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)


class MachoIdentificatorDto(StellarObjectIdentificatorDto):
    macho_id: str
    perv: float
    perr: float


class MachoPlugin(DefaultCatalogPlugin[MachoIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "MACHO",
            "We have taken ~27,000 images with this system since June 1992. Analysis of a subset of these data has yielded databases containing light curves in two colors for 8 million stars in the LMC and 10 million in the bulge of the Milky Way. A search for microlensing has turned up four candidates toward the Large Magellanic Cloud and 45 toward the Galactic Bulge. Papers describing these results can be found in the Publications section of the MACHO Web page. ",
            "https://wwwmacho.anu.edu.au/",
            True,
        )
        self._http_client = httpx.Client(timeout=10.0)
        self._vizier = Vizier()

    def _data_url(self, ident: MachoIdentificatorDto) -> str:
        return f"https://cdsarc.cds.unistra.fr/viz-bin/nph-Plot/Vgraph/txt?J/AJ/134/1963/./L/{ident.macho_id}/{ident.perr}/{ident.perv}&LC=Instrumental&P=0"

    def list_objects(
        self,
        coords: SkyCoord,
        radius_arcsec: float,
        plugin_id: UUID,
        resources_dir: Path,
    ) -> Iterator[list[MachoIdentificatorDto]]:
        result = self._vizier.query_region(
            coords, radius=radius_arcsec * u.arcsec, catalog="J/AJ/134/1963"
        )

        if len(result) <= 0:
            # no records found
            return

        result_table = result[0]
        targets: list[MachoIdentificatorDto] = []

        for row_idx in range(len(result_table)):
            macho_id = result_table["MACHO"][row_idx]
            perv = result_table["PerV"][row_idx]
            perr = result_table["PerR"][row_idx]
            ra_deg = result_table["RAJ2000"][row_idx]
            dec_deg = result_table["DEJ2000"][row_idx]

            target_coords = SkyCoord(ra=ra_deg, dec=dec_deg, unit=(u.hourangle, u.deg))

            targets.append(
                MachoIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=target_coords.ra.deg,
                    dec_deg=target_coords.dec.deg,
                    name=macho_id,
                    dist_arcsec=coords.separation(target_coords).arcsec,
                    macho_id=macho_id,
                    perr=perr,
                    perv=perv,
                )
            )

        if targets != []:
            yield targets

    def get_photometric_data(
        self, identificator: MachoIdentificatorDto, csv_path: Path, resources_dir: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        # data format:
        # JD-2400000	[mag]	(error)

        resp = self._http_client.get(self._data_url(identificator))
        resp.raise_for_status()

        batch: list[PhotometricDataDto] = []

        with open(csv_path, "w") as csv_file:
            csv_file.write("# JD-2400000, mag, mag_err\n")
            csv_file.write("JD,mag,mag_err\n")

            for line in resp.iter_lines():
                if not line.startswith("#"):
                    if len(batch) > self.batch_limit():
                        yield batch
                        batch = []

                    row = line.split()

                    jd = float(row[0]) + 2400000
                    mag = float(row[1])
                    mag_err = float(row[2])

                    csv_file.write(f"{jd},{mag},{mag_err}\n")

                    # convert JD_UTC to BJD_TDB
                    bjd = self._to_bjd_tdb(
                        jd,
                        time_format="jd",
                        time_scale="utc",
                        reference_frame="geocentric",
                        ra_deg=identificator.ra_deg,
                        dec_deg=identificator.dec_deg,
                    )

                    batch.append(
                        PhotometricDataDto(
                            plugin_id=identificator.plugin_id,
                            julian_date=bjd,
                            magnitude=mag,
                            magnitude_error=mag_err,
                            light_filter=None,
                        )
                    )

        if batch != []:
            yield batch
