import re
import time
from pathlib import Path
from typing import Iterator
from uuid import UUID

import httpx
import pandas as pd
from astropy.coordinates import SkyCoord

from src.core.config.config import settings
from src.plugin.interface.catalog_plugin import DefaultCatalogPlugin
from src.plugin.interface.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)


class AtlasIdentificatorDto(StellarObjectIdentificatorDto):
    pass


class AtlasPlugin(DefaultCatalogPlugin[AtlasIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "ATLAS",
            "Asteroid Terrestrial-impact Last Alert System is an asteroid impact early warning system developed by the University of Hawaii and funded by NASA. It consists of four telescopes (Hawaii ×2, Chile, South Africa), which automatically scan the whole sky several times every night looking for moving objects.",
            "https://fallingstar-data.com/forcedphot/",
            False,
        )
        self._http_client = httpx.Client(timeout=10.0)
        self._base_url = "https://fallingstar-data.com/forcedphot"

    def list_objects(
        self,
        coords: SkyCoord,
        radius_arcsec: float,
        plugin_id: UUID,
        resources_dir: Path,
    ) -> Iterator[list[AtlasIdentificatorDto]]:
        yield [
            AtlasIdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=coords.ra.deg,
                dec_deg=coords.dec.deg,
                name=None,
                dist_arcsec=0,
            )
        ]

    def get_photometric_data(
        self, identificator: AtlasIdentificatorDto, csv_path: Path, resources_dir: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        headers = {
            "Authorization": f"Token {settings.ATLAS_TOKEN}",
            "Accept": "application/json",
        }

        task_url = None
        while not task_url:
            resp = self._http_client.post(
                f"{self._base_url}/queue/",
                headers=headers,
                data={
                    "radeclist": f"{identificator.ra_deg} {identificator.dec_deg}",
                    "mjd_max": None,
                    "mjd_min": None,
                },
            )
            resp_json = resp.json()[0]
            if resp.status_code == 201:  # successfully queued
                task_url = resp_json["url"]
            elif resp.status_code == 429:  # throttled
                message = resp_json["detail"]
                t_sec = re.findall(r"available in (\d+) seconds", message)
                t_min = re.findall(r"available in (\d+) minutes", message)
                if t_sec:
                    waittime = int(t_sec[0])
                elif t_min:
                    waittime = int(t_min[0]) * 60
                else:
                    waittime = 10
                time.sleep(waittime)
            else:
                resp.raise_for_status()

        result_url = None
        while not result_url:
            resp = self._http_client.get(task_url, headers=headers)
            resp.raise_for_status()
            json_resp = resp.json()

            if resp.status_code == 200:  # HTTP OK
                if json_resp["finishtimestamp"]:
                    result_url = json_resp["result_url"]
                    break
                time.sleep(5)

        with self._http_client.stream("GET", result_url, headers=headers) as resp:
            resp.raise_for_status()
            with open(csv_path, "wb") as csv_file:
                for chunk in resp.iter_bytes(1024 * 1024):
                    csv_file.write(chunk)

        # if we'll be making a lot of requests, keep the web queue from being
        # cluttered (and reduce server storage usage) by sending a delete operation
        self._http_client.delete(task_url, headers=headers)

        for chunk in pd.read_csv(
            csv_path,
            chunksize=50_000,
            sep=r"\s+",
        ):
            chunk = chunk.rename(columns={"###MJD": "MJD"})

            # filter based on
            # https://fallingstar-data.com/forcedphot/faq/
            mask = (
                (chunk["m"] != 0)
                & (chunk["duJy"] < 10000)
                & (chunk["err"] == 0)
                & (chunk["x"].between(100, 10460))
                & (chunk["y"].between(100, 10460))
                & (chunk["maj"].between(1.6, 5))
                & (chunk["min"].between(1.6, 5))
                & (chunk["apfit"].between(-1, -0.1))
                & (chunk["mag5sig"] > 17)
                & (chunk["Sky"] > 17)
            )
            filtered_chunk = chunk[mask]

            batch: list[PhotometricDataDto] = []
            for mjd, mag, mag_err, photometric_filter in zip(
                filtered_chunk["MJD"],
                filtered_chunk["m"],
                filtered_chunk["dm"],
                filtered_chunk["F"],
            ):
                # convert MJD_UTC to BJD_TDB
                bjd = self._to_bjd_tdb(
                    mjd,
                    time_format="mjd",
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
                        light_filter=photometric_filter,
                    )
                )

            yield batch
