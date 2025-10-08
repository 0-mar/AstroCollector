from typing import Generator
from uuid import UUID
import random

from astropy.coordinates import SkyCoord

from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)


class DummyIdentificatorDto(StellarObjectIdentificatorDto):
    test_attr: str


class DummyPlugin(CatalogPlugin[DummyIdentificatorDto]):
    def __init__(self) -> None:
        super().__init__()
        self._directly_identifies_objects = True
        self._description = "DASCH was the project to digitize the Harvard College Observatory’s Astronomical Photographic Glass Plate Collection for scientific applications. This enormous — multi-decade — undertaking was completed in 2024. Its legacy is DASCH Data Release 7, an extraordinary dataset that enables scientific study of the entire night sky on 100-year timescales."
        self._catalog_url = "https://dasch.cfa.harvard.edu/"

    def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> Generator[list[DummyIdentificatorDto]]:
        yield [
            DummyIdentificatorDto(
                plugin_id=plugin_id,
                ra_deg=0.0,
                dec_deg=0.0,
                dist_arcsec=0,
                name="dummy",
                test_attr="test_attr_value",
            )
        ]

    def get_photometric_data(
        self, identificator: DummyIdentificatorDto
    ) -> Generator[list[PhotometricDataDto]]:
        for _ in range(10):
            yield [
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=i,
                    magnitude=5 + random.random() * 4,
                    magnitude_error=random.random() * 3,
                    light_filter="dummy",
                )
                for i in range(20000)
            ]
