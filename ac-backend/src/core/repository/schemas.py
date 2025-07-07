from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseIdDto(BaseDto):
    id: UUID
