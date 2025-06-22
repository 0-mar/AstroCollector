from abc import ABC, abstractmethod
from typing import TypeVar, List, Generic

from src.core.integration.schemas import IdentificatorModel, PhotometricDataModel

T = TypeVar("T", bound=IdentificatorModel)


class PhotometricCataloguePlugin(Generic[T], ABC):
    @abstractmethod
    def list_objects(
        self, ra_deg: float, dec_deg: float, radius_arcsec: float
    ) -> List[T]:
        pass

    @abstractmethod
    def get_photometric_data(self, identificator: T) -> List[PhotometricDataModel]:
        pass
