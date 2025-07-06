from src.core.repository.schemas import BaseDto


class SearchQueryRequestDto(BaseDto):
    right_ascension_deg: float
    declination_deg: float
    radius_arcsec: float = 30.0


class FindObjectQueryRequestDto(BaseDto):
    name: str
