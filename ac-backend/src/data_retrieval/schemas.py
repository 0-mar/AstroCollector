from typing import Any
from uuid import UUID

from src.core.repository.schemas import BaseIdDto


class EnrichedStellarObjectIdentifier(BaseIdDto):
    """
    Represents a stellar object identifier enriched by the task ID the identifier was retrieved in
    """

    task_id: UUID
    identifier: dict[str, Any]
