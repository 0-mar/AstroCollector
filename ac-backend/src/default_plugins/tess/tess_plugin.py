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


class TessStellarObjectIdentificatorDto(StellarObjectIdentificatorDto):
    tic: str


class TessPlugin(CatalogPlugin[TessStellarObjectIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__()
        self._directly_identifies_objects = True

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[TessStellarObjectIdentificatorDto]]:
        search_results: SearchResult = search_lightcurve(
            coords, radius=radius_arcsec, mission="TESS", author="SPOC"
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
                TessStellarObjectIdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=s_ra,
                    dec_deg=s_dec,
                    name=target_name,
                    dist_arcsec=float(distance),
                    tic=target_name,
                )
                for target_name, s_ra, s_dec, distance in unique_targets.iterrows(
                    "target_name", "s_ra", "s_dec", "distance"
                )
            ]

        # search for targets in the TIC (Tess Input Catalog)
        # search_table: Table = Catalogs.query_region(coords, radius=0.08333, catalog="TIC")
        #
        # chunk: list[TessStellarObjectIdentificatorDto] = []
        # for i in range(len(search_table)):
        #     if len(chunk) >= self.batch_limit():
        #         yield chunk
        #         chunk = []
        #
        #     tic = search_table['ID'][i]
        #     ra = search_table['ra'][i]
        #     dec = search_table['dec'][i]
        #     dist_arcsec = search_table['dstArcSec'][i]
        #     chunk.append(
        #         TessStellarObjectIdentificatorDto(
        #             plugin_id=plugin_id,
        #             ra_deg=ra,
        #             dec_deg=dec,
        #             name=None,
        #             dist_arcsec=float(dist_arcsec),
        #             tic=tic,
        #         )
        #     )
        #
        # if chunk != []:
        #     yield chunk

    def get_photometric_data(
        self, identificator: TessStellarObjectIdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        target = f"TIC {identificator.tic}"

        search_results: SearchResult = search_lightcurve(
            target, mission="TESS", author="SPOC"
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

                mag = -2.5 * math.log10(flux.value) + 20.44
                mag_err = (2.5 / math.log(10)) * (flux_err.value / flux.value)

                chunk.append(
                    PhotometricDataDto(
                        plugin_id=identificator.plugin_id,
                        julian_date=time.jd,
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

    def _write_raw_photometric_data_to_csv(
        self, path: Path, identificator: TessStellarObjectIdentificatorDto
    ) -> None:
        target = f"TIC {identificator.tic}"

        search_results: SearchResult = search_lightcurve(
            target, mission="TESS", author="SPOC"
        )

        header_written = False
        for search_result in search_results:
            try:
                # https://heasarc.gsfc.nasa.gov/docs/tess/Target-Pixel-File-Tutorial.html
                # downloads TESS target pixel file
                lightcurve = search_result.download()

            except LightkurveError:
                # error when downloading the lightcurve file
                continue

            df = lightcurve.to_pandas()
            sector = getattr(lightcurve, "sector", None) or lightcurve.meta.get(
                "SECTOR"
            )
            camera = getattr(lightcurve, "camera", None) or lightcurve.meta.get(
                "CAMERA"
            )
            ccd = getattr(lightcurve, "ccd", None) or lightcurve.meta.get("CCD")
            df["sector"] = sector
            df["camera"] = camera
            df["ccd"] = ccd

            # append to the CSV file
            df.to_csv(
                "test.csv",
                mode="a" if header_written else "w",
                header=not header_written,
                index=False,
            )
            header_written = True
