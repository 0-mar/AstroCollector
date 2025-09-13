import math
from abc import abstractmethod
from typing import AsyncIterator, List
from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy.table import Table

from fastapi.concurrency import run_in_threadpool
from lightkurve import SearchResult, search_lightcurve, LightkurveError

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)


class MastStellarObjectIdentificatorDto(StellarObjectIdentificatorDto):
    id: str


class MastPlugin(CatalogPlugin[MastStellarObjectIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__()
        self._directly_identifies_objects = True

    @abstractmethod
    def _get_target(self) -> str:
        # TIC, KIC, EPIC
        pass

    @abstractmethod
    def _get_mission(self) -> str:
        # TESS, Kepler, K2
        pass

    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> AsyncIterator[List[MastStellarObjectIdentificatorDto]]:
        sr: SearchResult = await run_in_threadpool(
            search_lightcurve,
            coords,
            radius=radius_arcsec / 3600,
            mission=self._get_mission(),
        )
        if len(sr.table) == 0:
            yield []
        else:
            mask = ["target_name", "s_ra", "s_dec", "distance"]
            unique_targets = Table.from_pandas(
                sr.table[mask]
                .to_pandas()
                .drop_duplicates("target_name")
                .reset_index(drop=True)
            )

            yield [
                MastStellarObjectIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=s_ra,
                    dec_deg=s_dec,
                    name=target_name,
                    dist_arcsec=float(distance),
                    id=target_name,
                )
                for target_name, s_ra, s_dec, distance in unique_targets.iterrows(
                    "target_name", "s_ra", "s_dec", "distance"
                )
            ]

    async def get_photometric_data(
        self, identificator: MastStellarObjectIdentificatorDto
    ) -> AsyncIterator[list[PhotometricDataDto]]:
        target = (
            identificator.id
            if not identificator.id.isdigit()
            else f"{self._get_target()} {identificator.id}"
        )

        lightcurves: SearchResult = await run_in_threadpool(
            search_lightcurve,
            target,
            mission=self._get_mission(),
        )

        for lightcurve in lightcurves:
            yield await run_in_threadpool(self.__get_lc_data, lightcurve, identificator)

    def __get_lc_data(
        self, lightcurve, identificator: MastStellarObjectIdentificatorDto
    ) -> list[PhotometricDataDto]:
        results: list[PhotometricDataDto] = []
        try:
            lightcurve_table = lightcurve.download()

        except LightkurveError:
            # error when downloading the lightcurve file
            return results

        for time, flux, flux_err in lightcurve_table.iterrows(
            "time", "flux", "flux_err"
        ):
            if math.isnan(flux.value) or flux.value < 0:
                continue
            mag = -2.5 * math.log10(flux.value) + 20.44
            mag_err = -2.5 * math.log10(flux_err.value) + 20.44

            if math.isnan(mag_err):
                continue

            results.append(
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=time.jd,
                    magnitude=mag,
                    magnitude_error=mag_err,
                    light_filter=None,
                )
            )

        return results
