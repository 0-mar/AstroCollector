import math
from pathlib import Path
from typing import Iterator
from uuid import UUID

from astropy.coordinates import SkyCoord
from astropy.table import Table

from lightkurve import SearchResult, LightkurveError, search_lightcurve, LightCurve

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)


class KeplerStellarObjectIdentificatorDto(StellarObjectIdentificatorDto):
    kic: str


class KeplerPlugin(CatalogPlugin[KeplerStellarObjectIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "Kepler",
            "The Kepler spacecraft was launched into an earth trailing orbit and stared at a 100 sq. degree patch of sky near Cygnus in order to measure the brightness variations of about 200,000 stars.  Its primary mission was to find exoplanets transiting these stars and to determine the prevalence of exoplanets in the Galaxy.  The Kepler spacecraft rotated by 90 degrees every 90 days in order to keep the solar panels pointing at the sun and thus the Kepler data is divided into 90-day quarters. Kepler only downloaded the pixels surrounding selected stars of interest at either a 30-minute or 1-minute cadence. The mission produced a flux time series for each star and searched these light curves for the presence of a transiting exoplanet.",
            "https://archive.stsci.edu/missions-and-data/kepler",
            True,
        )

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[KeplerStellarObjectIdentificatorDto]]:
        search_results: SearchResult = search_lightcurve(
            coords, radius=radius_arcsec, mission="Kepler", author="Kepler"
        )

        if len(search_results.table) == 0:
            return
        else:
            mask = ["target_name", "s_ra", "s_dec", "distance"]
            unique_targets = Table.from_pandas(
                search_results.table[mask]
                .to_pandas()
                .drop_duplicates("target_name")
                .reset_index(drop=True)
            )

            yield [
                KeplerStellarObjectIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=s_ra,
                    dec_deg=s_dec,
                    name=target_name,
                    dist_arcsec=float(distance),
                    kic=target_name,
                )
                for target_name, s_ra, s_dec, distance in unique_targets.iterrows(
                    "target_name", "s_ra", "s_dec", "distance"
                )
            ]

    def get_photometric_data(
        self, identificator: KeplerStellarObjectIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        target = f"{identificator.kic}"

        search_results: SearchResult = search_lightcurve(
            target, mission="Kepler", author="Kepler"
        )

        # https://heasarc.gsfc.nasa.gov/docs/tess/LightCurveFile-Object-Tutorial.html

        chunk: list[PhotometricDataDto] = []
        header_written = False
        for search_result in search_results:
            try:
                # https://heasarc.gsfc.nasa.gov/docs/tess/Target-Pixel-File-Tutorial.html
                # downloads TESS target pixel file
                lightcurve = search_result.download().remove_nans()

            except LightkurveError:
                # error when downloading the lightcurve file
                continue

            # lightcurve = target_pixel_file.to_lightcurve(aperture_mask=target_pixel_file.pipeline_mask).remove_nans()
            self.__write_to_csv(header_written, lightcurve, csv_path)
            header_written = True

            for time, flux, flux_err in lightcurve.iterrows("time", "flux", "flux_err"):
                if len(chunk) >= self.batch_limit():
                    yield chunk
                    chunk = []

                if flux.value <= 0:
                    continue

                mag = -2.5 * math.log10(flux.value) + 12.0
                mag_err = (2.5 / math.log(10)) * (flux_err.value / flux.value)

                chunk.append(
                    PhotometricDataDto(
                        plugin_id=identificator.plugin_id,
                        julian_date=time.tdb.jd,
                        magnitude=mag,
                        magnitude_error=mag_err,
                        light_filter=None,
                    )
                )

        if chunk != []:
            yield chunk

    def __write_to_csv(
        self, header_written: bool, lightcurve: LightCurve, path: Path
    ) -> None:
        df = lightcurve.to_pandas()
        sector = getattr(lightcurve, "sector", None) or lightcurve.meta.get("SECTOR")
        camera = getattr(lightcurve, "camera", None) or lightcurve.meta.get("CAMERA")
        ccd = getattr(lightcurve, "ccd", None) or lightcurve.meta.get("CCD")
        df["sector"] = sector
        df["camera"] = camera
        df["ccd"] = ccd

        # append to the CSV file
        df.to_csv(
            path,
            mode="a" if header_written else "w",
            header=not header_written,
            index=False,
        )
