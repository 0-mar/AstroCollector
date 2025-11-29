from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.tasks.model import Task, PhotometricData, StellarObjectIdentifier
from src.tasks.types import TaskStatus, TaskType


@pytest.mark.asyncio
class TestTaskModel:
    async def test_task_creation(self, db_session: AsyncSession):
        task = Task(task_type=TaskType.object_search)
        db_session.add(task)
        await db_session.commit()

        assert task.id is not None
        assert task.status == TaskStatus.in_progress
        assert task.task_type == TaskType.object_search
        assert isinstance(task.created_at, datetime)

    async def test_task_relationships(self, db_session: AsyncSession):
        task = Task(task_type=TaskType.photometric_data)
        db_session.add(task)
        await db_session.flush()

        photo_data = PhotometricData(
            task_id=task.id,
            plugin_id=uuid4(),
            julian_date=2459000.5,
            magnitude=12.5,
            magnitude_error=0.01,
            light_filter="V",
        )

        identifier = StellarObjectIdentifier(
            task_id=task.id,
            identifier={"catalog": "SIMBAD", "id": "HD 1234"},
        )

        db_session.add(photo_data)
        db_session.add(identifier)
        await db_session.flush()

        result = await db_session.execute(
            select(Task)
            .options(
                selectinload(Task.photometric_data),
                selectinload(Task.identifiers),
            )
            .where(Task.id == task.id)
        )
        db_task = result.scalar_one()

        assert len(db_task.photometric_data) == 1
        assert len(db_task.identifiers) == 1
        assert db_task.photometric_data[0].magnitude == 12.5
        assert db_task.identifiers[0].identifier["catalog"] == "SIMBAD"

    async def test_cascade_delete(self, db_session: AsyncSession):
        task = Task(task_type=TaskType.photometric_data)
        db_session.add(task)
        await db_session.flush()

        photo_data = PhotometricData(
            task_id=task.id,
            plugin_id=uuid4(),
            julian_date=2459000.5,
            magnitude=12.5,
            magnitude_error=0.01,
        )

        db_session.add(photo_data)
        await db_session.flush()

        await db_session.delete(task)
        await db_session.flush()

        # Verify photometric data is also deleted
        result = await db_session.execute(
            select(PhotometricData).where(PhotometricData.task_id == task.id)
        )
        remaining_data = result.scalars().all()
        assert remaining_data == []


@pytest.mark.asyncio
class TestPhotometricDataModel:
    async def test_photometric_data_creation(self, db_session: AsyncSession):
        task = Task(task_type=TaskType.photometric_data)
        db_session.add(task)
        await db_session.flush()

        photo_data = PhotometricData(
            task_id=task.id,
            plugin_id=uuid4(),
            julian_date=2459000.5,
            magnitude=12.5,
            magnitude_error=0.01,
            light_filter="V",
        )
        db_session.add(photo_data)
        await db_session.flush()

        result = await db_session.execute(
            select(PhotometricData).where(PhotometricData.id == photo_data.id)
        )
        db_photo = result.scalar_one()

        assert db_photo.id is not None
        assert db_photo.task_id == task.id
        assert db_photo.julian_date == 2459000.5
        assert db_photo.magnitude == 12.5
        assert db_photo.magnitude_error == 0.01
        assert db_photo.light_filter == "V"

    async def test_photometric_data_without_filter(self, db_session: AsyncSession):
        task = Task(task_type=TaskType.photometric_data)
        db_session.add(task)
        await db_session.flush()

        photo_data = PhotometricData(
            task_id=task.id,
            plugin_id=uuid4(),
            julian_date=2459000.5,
            magnitude=12.5,
            magnitude_error=0.01,
        )
        db_session.add(photo_data)
        await db_session.flush()

        result = await db_session.execute(
            select(PhotometricData).where(PhotometricData.id == photo_data.id)
        )
        db_photo = result.scalar_one()

        assert db_photo.light_filter is None


@pytest.mark.asyncio
class TestStellarObjectIdentifierModel:
    async def test_identifier_creation(self, db_session: AsyncSession):
        task = Task(task_type=TaskType.object_search)
        db_session.add(task)
        await db_session.flush()

        identifier_data = {
            "catalog": "SIMBAD",
            "id": "HD 1234",
            "ra": 123.456,
            "dec": -12.345,
        }
        identifier = StellarObjectIdentifier(
            task_id=task.id,
            identifier=identifier_data,
        )
        db_session.add(identifier)
        await db_session.flush()

        result = await db_session.execute(
            select(StellarObjectIdentifier).where(
                StellarObjectIdentifier.id == identifier.id
            )
        )
        db_identifier = result.scalar_one()

        assert db_identifier.id is not None
        assert db_identifier.task_id == task.id
        assert db_identifier.identifier == identifier_data
        assert db_identifier.identifier["catalog"] == "SIMBAD"

    async def test_complex_identifier_structure(self, db_session: AsyncSession):
        task = Task(task_type=TaskType.object_search)
        db_session.add(task)
        await db_session.flush()

        complex_identifier = {
            "primary": {"catalog": "SIMBAD", "id": "HD 1234"},
            "aliases": ["HIP 1234", "TYC 1234-5678-1"],
            "coordinates": {"ra": 123.456, "dec": -12.345},
            "metadata": {"source": "query", "confidence": 0.95},
        }

        identifier = StellarObjectIdentifier(
            task_id=task.id,
            identifier=complex_identifier,
        )
        db_session.add(identifier)
        await db_session.flush()

        result = await db_session.execute(
            select(StellarObjectIdentifier).where(
                StellarObjectIdentifier.id == identifier.id
            )
        )
        db_identifier = result.scalar_one()

        assert db_identifier.identifier["primary"]["id"] == "HD 1234"
        assert len(db_identifier.identifier["aliases"]) == 2
        assert db_identifier.identifier["metadata"]["confidence"] == 0.95
