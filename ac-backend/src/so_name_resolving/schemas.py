from src.core.repository.schemas import BaseDto


class StellarObjectNameDto(BaseDto):
    name: str


class ResolvedCoordsDto(BaseDto):
    ra_deg: float
    dec_deg: float
