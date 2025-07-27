from abc import ABC, abstractmethod
from typing import TypeVar, List, Generic
from uuid import UUID

from aiohttp import ClientSession
from astropy.coordinates import SkyCoord

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)

T = TypeVar("T", bound=StellarObjectIdentificatorDto)


class PhotometricCataloguePlugin(Generic[T], ABC):
    _http_client: ClientSession

    def __init__(self) -> None:
        pass

    async def init_plugin(self):
        self._http_client = ClientSession()

    async def close_session(self):
        await self._http_client.close()

    @abstractmethod
    async def list_objects(
        self, coords: SkyCoord, radius_arcsec: float, plugin_id: UUID
    ) -> List[T]:
        pass

    @abstractmethod
    async def get_photometric_data(self, identificator: T) -> List[PhotometricDataDto]:
        pass
