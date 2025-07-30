import datetime
from uuid import UUID

import sqlalchemy
from sqlalchemy import Double, func, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.database import DbEntity
from src.tasks.types import TaskStatus


class Task(DbEntity):
    __tablename__ = "ac_task"

    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.in_progress)
    created: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class PhotometricData(DbEntity):
    """."""

    __tablename__ = "ac_photometric_data"

    task_id: Mapped[UUID] = mapped_column(sqlalchemy.Uuid)
    plugin_id: Mapped[UUID] = mapped_column(sqlalchemy.Uuid)

    julian_date: Mapped[float] = mapped_column(Double, nullable=False)
    magnitude: Mapped[float] = mapped_column(Double, nullable=False)
    magnitude_error: Mapped[float] = mapped_column(Double, nullable=False)
    b_magnitude: Mapped[float] = mapped_column(Double, nullable=True)
    b_magnitude_error: Mapped[float] = mapped_column(Double, nullable=True)
    v_magnitude: Mapped[float] = mapped_column(Double, nullable=True)
    v_magnitude_error: Mapped[float] = mapped_column(Double, nullable=True)


class StellarObjectIdentifier(DbEntity):
    """Represents stellar object identifiers returned by a catalogue.
    The identifier format can vary, thus we are using JSONB type to store them."""

    __tablename__ = "ac_stellar_object_identifier"

    task_id: Mapped[UUID] = mapped_column(sqlalchemy.Uuid)
    identifier = mapped_column(JSONB, nullable=False)
