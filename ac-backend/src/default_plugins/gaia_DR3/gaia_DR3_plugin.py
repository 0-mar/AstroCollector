import math
from pathlib import Path
from typing import Iterator
from uuid import UUID

from astropy.coordinates import SkyCoord

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)

from astroquery.gaia import Gaia


class GaiaDR3IdentificatorDto(StellarObjectIdentificatorDto):
    source_id: str


class GaiaDR3Plugin(CatalogPlugin[GaiaDR3IdentificatorDto]):
    def __init__(self) -> None:
        super().__init__(
            "Gaia DR3",
            "Gaia is a European space mission providing astrometry, photometry, and spectroscopy of nearly 2000 million stars in the Milky Way as well as significant samples of extragalactic and solar system objects. The Gaia ESA Archive contains deduced positions, parallaxes, proper motions, radial velocities, and brightness measurements.",
            "https://www.cosmos.esa.int/web/gaia/data-release-3",
            True,
        )

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Iterator[list[GaiaDR3IdentificatorDto]]:
        adql = f"""
        SELECT source_id, ra, dec, phot_g_mean_mag
        FROM gaiadr3.gaia_source
        WHERE has_epoch_photometry = 'True' AND 1=CONTAINS(
          POINT('ICRS', ra, dec),
          CIRCLE('ICRS', {coords.ra.deg}, {coords.dec.deg}, {radius_arcsec / 3600})
        )
        """
        job = Gaia.launch_job_async(adql)
        result_table = job.get_results()

        chunk: list[GaiaDR3IdentificatorDto] = []
        for source_id, ra, dec in result_table.iterrows("source_id", "ra", "dec"):
            if len(chunk) > self.batch_limit():
                yield chunk
                chunk = []

            target = SkyCoord(ra=ra, dec=dec, unit="deg")
            dist_arcsec = coords.separation(target).arcsec

            chunk.append(
                GaiaDR3IdentificatorDto(
                    plugin_id=plugin_id,
                    ra_deg=ra,
                    dec_deg=dec,
                    source_id=str(source_id),
                    name=str(source_id),
                    dist_arcsec=dist_arcsec,
                )
            )

        if chunk != []:
            yield chunk

    def get_photometric_data(
        self, identificator: GaiaDR3IdentificatorDto, csv_path: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        # for DB columns, see:
        # https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_photometry/ssec_dm_epoch_photometry.html

        # data retrieval tutorial:
        # https://www.cosmos.esa.int/web/gaia-users/archive/datalink-products#Tutorial:--Retrieve-(all)-the-DataLink-products-associated-to-a-sample

        retrieval_type = "EPOCH_PHOTOMETRY"  # Options are: 'EPOCH_PHOTOMETRY', 'MCMC_GSPPHOT', 'MCMC_MSC', 'XP_SAMPLED', 'XP_CONTINUOUS', 'RVS', 'ALL'
        data_structure = "INDIVIDUAL"  # Options are: 'INDIVIDUAL' and 'RAW'
        data_release = "Gaia DR3"  # Options are: 'Gaia DR3' (default), 'Gaia DR2'
        datalink = Gaia.load_data(
            ids=[identificator.source_id],
            data_release=data_release,
            retrieval_type=retrieval_type,
            data_structure=data_structure,
            verbose=False,
        )
        key_list = list(datalink.keys())
        # no records found in the table.
        # the key_list should contain only 1 record, as we are selecting only 1 source id

        if len(key_list) < 1:
            return

        key = key_list[0]

        votable = datalink[key][0]  # Select the first (and only) element of the list
        result_table = votable.to_table()

        result_table.write(csv_path, format="ascii.csv", overwrite=True)

        mask = result_table["rejected_by_photometry"] == False  # noqa: E712
        table = result_table[mask]
        chunk: list[PhotometricDataDto] = []
        for i in range(len(table)):
            if len(chunk) >= self.batch_limit():
                yield chunk
                chunk = []

            # Values are BJD_TCB timestamps
            # The reference epoch for time are (BJD) 2010-01-01T00:00:00.
            # 2010-01-01T00:00:00 (UTC) == 2455197.5 (JD)
            bjd_tcb = table["g_transit_time"][i] + 2455197.5
            g_mag = table["g_transit_mag"][i]
            # TODO convert to magnitude error?
            g_mag_err = (2.5 / math.log(10)) * (
                table["g_transit_flux_error"][i] / table["g_transit_flux"][i]
            )

            # convert BJD_TCB to BJD_TDB
            bjd = self._to_bjd_tdb(
                bjd_tcb,
                time_format="jd",
                time_scale="tcb",
                reference_frame="barycentric",
                ra_deg=identificator.ra_deg,
                dec_deg=identificator.dec_deg,
            )

            chunk.append(
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=bjd,
                    magnitude=g_mag,
                    magnitude_error=g_mag_err,
                    light_filter="G",
                )
            )

        if chunk != []:
            yield chunk
