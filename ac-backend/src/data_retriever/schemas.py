from uuid import UUID

from src.core.repository.schemas import BaseDto


class ConeSearchRequestDto(BaseDto):
    plugin_id: UUID
    right_ascension_deg: float
    declination_deg: float
    radius_arcsec: float = 30.0


class FindObjectRequestDto(BaseDto):
    plugin_id: UUID
    name: str
