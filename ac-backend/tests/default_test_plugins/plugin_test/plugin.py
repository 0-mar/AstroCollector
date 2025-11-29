from pathlib import Path
from typing import Iterator
from uuid import UUID

from astropy.coordinates import SkyCoord

from src.plugin.interface.catalog_plugin import DefaultCatalogPlugin
from src.plugin.interface.schemas import (
    PhotometricDataDto,
    StellarObjectIdentificatorDto,
)

REFCAT_APASS = "apass"


class IdentificatorDtoTest(StellarObjectIdentificatorDto):
    test: int
    value: str


class PluginTest(DefaultCatalogPlugin[IdentificatorDtoTest]):
    # https://dasch.cfa.harvard.edu/dr7/web-apis/
    def __init__(self) -> None:
        super().__init__(
            "Test",
            "Test plugin",
            "https://google.com",
            True,
        )

    def list_objects(
        self,
        coords: SkyCoord,
        radius_arcsec: float,
        plugin_id: UUID,
        resources_dir: Path,
    ) -> Iterator[list[IdentificatorDtoTest]]:
        yield [
            IdentificatorDtoTest(
                name="Test2",
                plugin_id=plugin_id,
                ra_deg=1,
                dec_deg=1,
                test=2,
                value="test2",
                dist_arcsec=0.1,
            ),
            IdentificatorDtoTest(
                name="Test",
                plugin_id=plugin_id,
                ra_deg=0,
                dec_deg=0,
                test=1,
                value="test",
                dist_arcsec=0.1,
            ),
        ]

    def get_photometric_data(
        self, identificator: IdentificatorDtoTest, csv_path: Path, resources_dir: Path
    ) -> Iterator[list[PhotometricDataDto]]:
        chunk = []
        for i in range(10):
            chunk.append(
                PhotometricDataDto(
                    plugin_id=identificator.plugin_id,
                    julian_date=i,
                    magnitude=i,
                    magnitude_error=i,
                    light_filter="V",
                )
            )
        yield chunk
