import math
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


class TessStellarObjectIdentificatorDto(StellarObjectIdentificatorDto):
    # TIC = TESS Input Catalog
    tic: int
    dstArcSec: float


class TessPlugin(PhotometricCataloguePlugin[TessStellarObjectIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__()

    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> list[TessStellarObjectIdentificatorDto]:
        search_results = await run_in_threadpool(
            Catalogs.query_region, coords, radius=radius_arcsec / 3600, catalog="TIC"
        )
        table = search_results["ID", "ra", "dec", "dstArcSec"]

        results = [
            TessStellarObjectIdentificatorDto(
                plugin_id=plugin_id, ra_deg=ra, dec_deg=dec, tic=id, dstArcSec=dstArcSec
            )
            for id, ra, dec, dstArcSec in table
        ]

        return results

    async def get_photometric_data(
        self, identificator: TessStellarObjectIdentificatorDto
    ) -> list[PhotometricDataDto]:
        lcs: SearchResult = search_lightcurve(
            f"TIC {identificator.tic}", mission="TESS"
        )

        results: list[PhotometricDataDto] = []
        for lc in lcs:
            try:
                lightcurve_table = await run_in_threadpool(lc.download)

            except LightkurveError:
                # error when downloading the lightcurve file
                continue

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

        return results
