from enum import Enum


class TaskStatus(Enum):
    in_progress = "IN_PROGRESS"
    completed = "COMPLETED"
    failed = "FAILED"
