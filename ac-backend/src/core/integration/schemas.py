from pydantic import BaseModel


class IdentificatorModel(BaseModel):
    ra_deg: float
    dec_deg: float


class PhotometricDataModel(BaseModel):
    julian_date: float
    magnitude: float
    error: float
