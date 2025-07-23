from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StellarObjectIdentificatorDto(BaseModel):
    model_config = ConfigDict(extra="allow")
    plugin_id: UUID
    ra_deg: float
    dec_deg: float


class PhotometricDataDto(BaseModel):
    # TODO include other mags, such as vmag or vmag err
    plugin_id: UUID
    julian_date: float
    magnitude: float
    error: float
