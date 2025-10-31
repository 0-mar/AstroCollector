import datetime
from uuid import UUID

import sqlalchemy
from sqlalchemy import Double, func, DateTime, String, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import DbEntity
from src.tasks.types import TaskStatus, TaskType


class Task(DbEntity):
    __tablename__ = "ac_task"

    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.in_progress)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    task_type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="task_type"), nullable=False
    )

    # By default, all related objects are lazy-loaded
    # https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#lazy-loading

    # passive_deletes=True on the relationships tells SQLAlchemy not to emit DELETEs for children,
    # because it is handled by the DB

    photometric_data: Mapped[list["PhotometricData"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )
    identifiers: Mapped[list["StellarObjectIdentifier"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class PhotometricData(DbEntity):
    """."""

    __tablename__ = "ac_photometric_data"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("ac_task.id", ondelete="CASCADE"), nullable=False
    )
    plugin_id: Mapped[UUID] = mapped_column(sqlalchemy.Uuid)

    julian_date: Mapped[float] = mapped_column(Double, nullable=False)
    magnitude: Mapped[float] = mapped_column(Double, nullable=False)
    magnitude_error: Mapped[float] = mapped_column(Double, nullable=False)
    light_filter: Mapped[str] = mapped_column(String, nullable=True)


class StellarObjectIdentifier(DbEntity):
    """Represents stellar object identifiers returned by a catalogue.
    The identifier format can vary, thus we are using JSONB type to store them."""

    __tablename__ = "ac_stellar_object_identifier"

    task_id: Mapped[UUID] = mapped_column(
        ForeignKey("ac_task.id", ondelete="CASCADE"), nullable=False
    )
    identifier = mapped_column(JSONB, nullable=False)
