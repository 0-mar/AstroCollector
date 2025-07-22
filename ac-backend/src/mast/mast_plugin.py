import math
from abc import abstractmethod
from uuid import UUID

from astropy.coordinates import SkyCoord

from fastapi.concurrency import run_in_threadpool
from lightkurve import SearchResult, search_lightcurve, LightkurveError

from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)

from astroquery.mast import Catalogs


class MastStellarObjectIdentificatorDto(StellarObjectIdentificatorDto):
    id: int
    dstArcSec: float


class MastPlugin(PhotometricCataloguePlugin[MastStellarObjectIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def _get_target(self, id: int) -> str:
        pass

    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> list[MastStellarObjectIdentificatorDto]:
        # querymethod: https://astroquery.readthedocs.io/en/latest/api.html
        search_results = await run_in_threadpool(
            Catalogs.query_region, coords, radius=radius_arcsec / 3600, catalog="TIC"
        )
        table = search_results["ID", "ra", "dec", "dstArcSec"]

        results = [
            MastStellarObjectIdentificatorDto(
                plugin_id=plugin_id, ra_deg=ra, dec_deg=dec, id=id, dstArcSec=dstArcSec
            )
            for id, ra, dec, dstArcSec in table
        ]

        return results

    async def get_photometric_data(
        self, identificator: MastStellarObjectIdentificatorDto
    ) -> list[PhotometricDataDto]:
        lcs: SearchResult = search_lightcurve(
            self._get_target(identificator.id), mission="TESS"
        )

        results: list[PhotometricDataDto] = []
        for lc in lcs:
            try:
                lightcurve_table = await run_in_threadpool(lc.download)

            except LightkurveError:
                # error when downloading the lightcurve file
                continue

            self.__get_lc_data(lightcurve_table, results, identificator)

        return results

    def __get_lc_data(self, lightcurve_table, results, identificator):
        # TODO check time units (is it really in JD?)
        for time, flux, flux_err in lightcurve_table.iterrows(
            "time", "flux", "flux_err"
        ):
            if math.isnan(flux.value) or flux.value < 0:
                continue
            mag = -2.5 * math.log10(flux.value) + 20.44
            mag_err = -2.5 * math.log10(flux_err.value) + 20.44

            results.append(
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=time.jd,
                    magnitude=mag,
                    error=mag_err,
                )
            )
