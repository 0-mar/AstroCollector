from typing import Any
from uuid import UUID

UUID_FIELDS = {"task_id", "id"}


def convert_uuid_fields(filters: dict[str, Any]) -> dict[str, Any]:
    for key in UUID_FIELDS:
        if key in filters and isinstance(filters[key], str):
            try:
                filters[key] = UUID(filters[key])
            except ValueError:
                raise ValueError(f"Invalid UUID format for '{key}'")

    return filters
