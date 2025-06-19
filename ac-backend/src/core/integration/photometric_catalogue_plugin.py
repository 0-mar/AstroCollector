from abc import ABC, abstractmethod
from typing import TypeVar, List

from src.core.integration.schemas import IdentificatorModel, PhotometricDataModel

T = TypeVar('T',  bound=IdentificatorModel)

class PhotometricCataloguePlugin(ABC):
    @abstractmethod
    def list_objects(self, ra_deg, dec_deg, radius_arcsec) -> List[T]:
        pass

    @abstractmethod
    def get_photometric_data(self, identificator: T) -> List[PhotometricDataModel]:
        pass