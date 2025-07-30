from typing import Any
from uuid import UUID

from src.core.repository.schemas import BaseIdDto


class StellarObjectIdentifierDto(BaseIdDto):
    task_id: UUID
    identifier: dict[str, Any]
