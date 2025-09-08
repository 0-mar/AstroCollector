import datetime

from src.core.repository.schemas import BaseIdDto, BaseDto


class PluginDto(BaseIdDto):
    name: str
    created_by: str
    created: datetime.datetime
    directly_identifies_objects: bool


class CreatePluginDto(BaseDto):
    name: str
    created_by: str
    directly_identifies_objects: bool


class UpdatePluginDto(BaseIdDto):
    name: str | None = None
    directly_identifies_objects: bool


class UpdatePluginFileDto(BaseIdDto):
    file_name: str
