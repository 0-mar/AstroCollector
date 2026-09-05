import datetime

from src.core.repository.schemas import BaseIdDto, BaseDto


class PluginResponse(BaseIdDto):
    name: str
    created_by: str
    created: datetime.datetime
    directly_identifies_objects: bool
    description: str
    catalog_url: str
    file_name: str | None


class PluginCreateRequest(BaseDto):
    name: str
    created_by: str
    directly_identifies_objects: bool
    catalog_url: str
    description: str


class PluginUpdateRequest(BaseIdDto):
    name: str | None = None
    directly_identifies_objects: bool | None = None
    description: str | None = None
    catalog_url: str | None = None


class PluginUpdateFileRequest(BaseIdDto):
    file_name: str
