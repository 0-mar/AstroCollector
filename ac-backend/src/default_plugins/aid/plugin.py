import os
import tempfile
from typing import List, AsyncIterator, Any, Generator
from uuid import UUID

import aiofiles
from astropy.coordinates import SkyCoord
from fastapi.concurrency import run_in_threadpool
import pandas as pd

from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)


class AidIdentificatorDto(StellarObjectIdentificatorDto):
    auid: str


class AidPlugin(PhotometricCataloguePlugin[AidIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__()

    def __list_url(self, ra: float, dec: float, radius: float) -> str:
        return f"https://vsx.aavso.org/index.php?view=api.list&ra={ra}&dec={dec}&radius={radius}&format=json"

    def __data_url(self, auid: str) -> str:
        return (
            f"http://vsx.aavso.org/index.php?view=api.delim&ident={auid}&delimiter=%7C"
        )

    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncIterator[List[AidIdentificatorDto]]:
        async with self._http_client.get(
            self.__list_url(coords.ra.deg, coords.dec.deg, radius_arcsec / 3600.0)
        ) as query_resp:
            query_data = await query_resp.json()

        yield await run_in_threadpool(
            self._process_objects_batch, query_data, plugin_id
        )

    def _process_objects_batch(
        self,
        query_data: dict[str, Any],
        plugin_id: UUID,
    ) -> list[AidIdentificatorDto]:
        results = []
        if query_data["VSXObjects"] == []:
            return results

        for record in query_data["VSXObjects"]["VSXObject"]:
            if "AUID" not in record:
                continue
            results.append(
                AidIdentificatorDto(
                    plugin_id=plugin_id,
                    auid=record["AUID"],
                    ra_deg=record["RA2000"],
                    dec_deg=record["Declination2000"],
                )
            )

        return results

    async def get_photometric_data(
        self, identificator: AidIdentificatorDto
    ) -> AsyncIterator[List[PhotometricDataDto]]:
        path = await self.__fetch_to_temp_csv(self.__data_url(identificator.auid))

        it = self.__get_chunk(path, identificator)

        while True:
            batch = await run_in_threadpool(next, it, None)

            if batch is None:
                os.remove(path)
                return

            if batch == []:
                continue

            yield batch

    async def __fetch_to_temp_csv(self, url: str) -> str:
        async with self._http_client.get(url) as resp:
            resp.raise_for_status()
            fd, path = tempfile.mkstemp(suffix=".csv")
            os.close(fd)
            try:
                async with aiofiles.open(path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 1024):
                        await f.write(chunk)
                return path
            except Exception:
                try:
                    os.remove(path)
                except OSError:
                    pass
                raise

    def __get_chunk(
        self, path: str, identificator: AidIdentificatorDto
    ) -> Generator[list[PhotometricDataDto]]:
        for chunk in pd.read_csv(
            path,
            chunksize=50_000,
            sep="|",
            usecols=["JD", "mag", "uncert", "band"],
            dtype={
                "JD": "float64",
                "mag": "float64",
                "uncert": "float64",
                "band": "str",
            },
            na_values=(""),
            on_bad_lines="skip",
        ):
            batch: list[PhotometricDataDto] = []
            chunk = chunk.dropna(subset=["JD", "mag", "uncert", "band"])
            for jd, mag, uncert, band in chunk.itertuples(index=False, name=None):
                batch.append(
                    PhotometricDataDto(
                        plugin_id=identificator.plugin_id,
                        julian_date=jd,
                        magnitude=mag,
                        magnitude_error=uncert,
                        light_filter=band,
                    )
                )
            yield batch
