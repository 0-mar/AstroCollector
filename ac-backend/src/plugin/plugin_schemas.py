import datetime

from src.core.repository.schemas import BaseIdDto, BaseDto


class PluginDto(BaseIdDto):
    name: str
    created_by: str
    created: datetime.datetime
    file_name: str | None


class CreatePluginDto(BaseDto):
    name: str
    created_by: str


class UpdatePluginDto(BaseIdDto):
    name: str | None = None


class UpdatePluginFileDto(BaseIdDto):
    file_name: str
