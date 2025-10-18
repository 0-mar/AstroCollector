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


class Mmt9IdentificatorDto(StellarObjectIdentificatorDto):
    radius_arcsec: float


class Mmt9Plugin(CatalogPlugin[Mmt9IdentificatorDto]):
    # http://survey.favor2.info/favor2/
    def __init__(self) -> None:
        super().__init__(
            "MMT9",
            "The Mini-MegaTORTORA (MMT-9) system is an unique multi-purpose wide-field monitoring instrument built for and owned by the Kazan Federal University, presently operated under an agreement between Kazan Federal University and Special Astrophysical Observatory, Russia.",
            "http://survey.favor2.info/favor2/",
            False,
        )
        self._url = "http://survey.favor2.info/favor2/photometry/json"
        self._http_client = httpx.Client(timeout=30.0)

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[Mmt9IdentificatorDto]]:
        query_params = {
            "coords": f"{coords.ra.deg} {coords.dec.deg} ",
            "sr": f"{radius_arcsec / 3600}",
            "sr_value": f"{radius_arcsec}",
            "sr_units": "arcsec",
            "name": "degrees",
            "ra": f"{coords.ra.deg}",
            "dec": f"{coords.dec.deg}",
        }
        query_resp = self._http_client.get(self._url, params=query_params)
        query_data = query_resp.json()

        if query_data["lcs"] == []:
            return

        # catalog does not group results by stellar object ID, so instead we treat measurements as one object.
        # It is up to the user to set appropriate radius
        yield [
            Mmt9IdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=coords.ra.deg,
                dec_deg=coords.dec.deg,
                radius_arcsec=radius_arcsec,
                name="",
                dist_arcsec=0,
            )
        ]

    def get_photometric_data(
        self, identificator: Mmt9IdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        query_params = {
            "coords": f"{identificator.ra_deg} {identificator.dec_deg} ",
            "sr": f"{identificator.radius_arcsec / 3600}",
            "sr_value": f"{identificator.radius_arcsec}",
            "sr_units": "arcsec",
            "name": "degrees",
            "ra": f"{identificator.ra_deg}",
            "dec": f"{identificator.dec_deg}",
        }
        query_resp = self._http_client.get(self._url, params=query_params)
        query_data = query_resp.json()

        chunk: list[PhotometricDataDto] = []

        with open(csv_path, mode="w") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=",")
            csv_writer.writerow(
                [
                    "filter",
                    "color",
                    "bv",
                    "times",
                    "mjds",
                    "xi",
                    "eta",
                    "mags",
                    "magerrs",
                    "flags",
                    "fwhms",
                    "channels",
                    "color_terms",
                    "stds",
                    "nstars",
                ]
            )

            for record in query_data["lcs"]:
                for i in range(len(record["mags"])):
                    csv_writer.writerow(
                        [
                            record["filter"],
                            record["color"],
                            record["bv"],
                            record["times"][i],
                            record["mjds"][i],
                            record["xi"][i],
                            record["eta"][i],
                            record["mags"][i],
                            record["magerrs"][i],
                            record["flags"][i],
                            record["fwhms"][i],
                            record["channels"][i],
                            record["color_terms"][i],
                            record["stds"][i],
                            record["nstars"][i],
                        ]
                    )

                    if len(chunk) >= self.batch_limit():
                        yield chunk
                        chunk = []

                    # convert MJD_UTC to BJD_TDB
                    bjd = self._to_bjd(
                        float(record["mjds"][i]),
                        format="mjd",
                        scale="utc",
                        ra_deg=identificator.ra_deg,
                        dec_deg=identificator.dec_deg,
                        is_hjd=False,
                    )

                    chunk.append(
                        PhotometricDataDto(
                            julian_date=bjd,
                            magnitude=record["mags"][i],
                            magnitude_error=record["magerrs"][i],
                            plugin_id=identificator.plugin_id,
                            light_filter=record["filter"],
                        )
                    )

        if chunk != []:
            yield chunk
