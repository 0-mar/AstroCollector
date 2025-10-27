from uuid import UUID

from pydantic import ConfigDict, field_serializer

from src.core.repository.schemas import BaseDto


class StellarObjectIdentificatorDto(BaseDto):
    """
    Represents a Data Transfer Object (DTO) for identifying stellar objects.

    This class is used to encapsulate information required for identifying stellar
    objects. Classes extending the basic identifier can add their own attributes.

    :ivar plugin_id: ID of the plugin that created this identifier.
    :ivar ra_deg: Right ascension of the stellar object, in degrees.
    :ivar dec_deg: Declination of the stellar object, in degrees.
    :ivar name: Optional name of the stellar object, if available.
    :ivar dist_arcsec: Distance from a reference point in arcseconds.
    """

    model_config = ConfigDict(extra="allow")
    plugin_id: UUID
    ra_deg: float
    dec_deg: float
    name: str | None
    dist_arcsec: float

    @field_serializer("plugin_id")
    def serialize_id(self, plugin_id: UUID, _info):
        return str(plugin_id)


class PhotometricDataDto(BaseDto):
    """
    Represents photometric measurements in unified format.

    :ivar plugin_id: ID of the plugin that created this record.
    :ivar julian_date: Julian date corresponding to the observation. The timestamp must be in the BJD_TDB. Please see _to_bjd_tdb in CatalogPlugin for more details.
    :ivar magnitude: Magnitude of the observed object.
    :ivar magnitude_error: Uncertainty associated with the magnitude.
    :ivar light_filter: Light filter applied during the observation, if available.
    """

    plugin_id: UUID
    julian_date: float
    magnitude: float
    magnitude_error: float
    light_filter: str | None
