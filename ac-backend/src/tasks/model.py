import datetime
from typing import List
from uuid import UUID

from sqlalchemy import Double, ForeignKey, func, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.database import DbEntity
from src.tasks.types import TaskStatus


class Task(DbEntity):
    __tablename__ = "ac_task"

    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.in_progress)
    results: Mapped[List["TaskResult"]] = relationship()
    created: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class TaskResult(DbEntity):
    task_id: Mapped[UUID] = mapped_column(ForeignKey("ac_task.id"))
    type: Mapped[str] = mapped_column(nullable=False)

    __tablename__ = "ac_task_result"
    __mapper_args__ = {"polymorphic_identity": "task_result", "polymorphic_on": "type"}


class PhotometricData(TaskResult):
    """."""

    __tablename__ = "ac_photometric_data"
    __mapper_args__ = {
        "polymorphic_identity": "photometric_data",
    }

    id: Mapped[UUID] = mapped_column(ForeignKey("ac_task_result.id"), primary_key=True)

    julian_date: Mapped[float] = mapped_column(Double, nullable=False)
    magnitude: Mapped[float] = mapped_column(Double, nullable=False)
    magnitude_err: Mapped[float] = mapped_column(Double, nullable=False)
    b_magnitude: Mapped[float] = mapped_column(Double, nullable=True)
    b_magnitude_err: Mapped[float] = mapped_column(Double, nullable=True)
    v_magnitude: Mapped[float] = mapped_column(Double, nullable=True)
    v_magnitude_err: Mapped[float] = mapped_column(Double, nullable=True)


class StellarObjectIdentifier(TaskResult):
    """Represents stellar object identifiers returned by a catalogue.
    The identifier format can vary, thus we are using JSONB type to store them."""

    __tablename__ = "ac_stellar_object_identifier"
    __mapper_args__ = {
        "polymorphic_identity": "stellar_object_identifier",
    }

    id: Mapped[UUID] = mapped_column(ForeignKey("ac_task_result.id"), primary_key=True)

    identifier = mapped_column(JSONB, nullable=False)
