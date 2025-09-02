from src.core.repository.schemas import BaseDto


class PhaseCurveDataDto(BaseDto):
    period: float | None
    epoch: float | None
    ra_deg: float | None
    dec_deg: float | None
    vsx_object_name: str | None
