from uuid import UUID

import sqlalchemy
from sqlalchemy import Double
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database.database import DbEntity


class TaskBase(DbEntity):
    __abstract__ = True

    task_id: Mapped[UUID] = mapped_column(sqlalchemy.Uuid, nullable=False, index=True)


class PhotometricData(TaskBase):
    """."""

    __tablename__ = "ac_photometric_data"

    julian_date: Mapped[float] = mapped_column(Double, nullable=False)
    magnitude: Mapped[float] = mapped_column(Double, nullable=False)
    magnitude_err: Mapped[float] = mapped_column(Double, nullable=False)
    b_magnitude: Mapped[float] = mapped_column(Double, nullable=True)
    b_magnitude_err: Mapped[float] = mapped_column(Double, nullable=True)
    v_magnitude: Mapped[float] = mapped_column(Double, nullable=True)
    v_magnitude_err: Mapped[float] = mapped_column(Double, nullable=True)


class StellarObjectIdentifier(TaskBase):
    """Represents stellar object identifiers returned by a catalogue.
    The identifier format can vary, thus we are using JSONB type to store them."""

    __tablename__ = "ac_stellar_object_identifier"

    identifier = mapped_column(JSONB, nullable=False)
