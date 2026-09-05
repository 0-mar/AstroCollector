from uuid import UUID

from src.core.repository.schemas import BaseDto


class ConeSearchRequest(BaseDto):
    plugin_id: UUID
    right_ascension_deg: float
    declination_deg: float
    radius_arcsec: float = 30.0


class FindObjectRequest(BaseDto):
    plugin_id: UUID
    name: str


class TaskCreatedResponse(BaseDto):
    task_id: UUID


class TaskStatusResponse(BaseDto):
    task_id: UUID
    status: str
