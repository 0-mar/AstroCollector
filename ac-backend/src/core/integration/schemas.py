from uuid import UUID

from pydantic import ConfigDict, field_serializer

from src.core.repository.schemas import BaseDto


class StellarObjectIdentificatorDto(BaseDto):
    model_config = ConfigDict(extra="allow")
    plugin_id: UUID
    ra_deg: float
    dec_deg: float

    @field_serializer("plugin_id")
    def serialize_id(self, plugin_id: UUID, _info):
        return str(plugin_id)


class PhotometricDataDto(BaseDto):
    plugin_id: UUID
    julian_date: float
    magnitude: float
    magnitude_error: float
    b_magnitude: float | None
    b_magnitude_error: float | None
    v_magnitude: float | None
    v_magnitude_error: float | None
