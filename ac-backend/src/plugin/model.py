import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.database import DbEntity
from sqlalchemy.sql import func


class Plugin(DbEntity):
    """Plugin model for database."""

    __tablename__ = "ac_plugin"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    file_name: Mapped[str] = mapped_column(String(100), nullable=True)
    directly_identifies_objects: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
