from src.core.repository.schemas import BaseDto


class StellarObjectNameRequest(BaseDto):
    name: str


class ResolvedCoordsDto(BaseDto):
    ra_deg: float
    dec_deg: float
