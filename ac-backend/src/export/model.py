import datetime

from sqlalchemy import DateTime, func, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import mapped_column, Mapped

from src.core.database.database import DbEntity
from src.export.types import ExportOption


class ExportFile(DbEntity):
    __tablename__ = "ac_export_file"

    file_name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    export_option: Mapped[ExportOption] = mapped_column(
        SAEnum(ExportOption, name="export_option"), nullable=False
    )
    task_set_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    """SHA-256 hash created from the task set and export option. Used for file lookup."""
