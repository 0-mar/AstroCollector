from enum import Enum


class TaskStatus(Enum):
    in_progress = "IN_PROGRESS"
    completed = "COMPLETED"
    failed = "FAILED"


class TaskType(Enum):
    object_search = "OBJECT_SEARCH"
    photometric_data = "PHOTOMETRIC_DATA"
