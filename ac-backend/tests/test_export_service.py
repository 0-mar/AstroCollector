import zipfile
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import aiofiles
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.config.config import settings
from src.core.repository.repository import Filters
from src.core.service.schemas import PaginationResponseDto
from src.export.model import ExportFile
from src.export.service import ExportService
from src.export.types import ExportOption
from src.plugin.interface.schemas import PhotometricDataDto


@pytest.fixture
def fake_export_repo():
    class FakeRepo:
        def __init__(self):
            self.saved: list[ExportFile] = []
            # (total, [ExportFile,...])
            self.find_result = (0, [])

        async def save(self, entity: ExportFile):
            self.saved.append(entity)
            return entity

        async def find(self, *args, **kwargs):
            return self.find_result

    return FakeRepo()


@pytest.fixture
def fake_plugin_service():
    class FakePluginService:
        def __init__(self):
            self.plugins = [
                SimpleNamespace(id=uuid4(), name="SourceA"),
                SimpleNamespace(id=uuid4(), name="SourceB"),
            ]

        async def list_plugins(self):
            return SimpleNamespace(data=self.plugins)

    return FakePluginService()


@pytest.fixture
def fake_data_service_single_page(fake_plugin_service):
    plugin_id = fake_plugin_service.plugins[0].id

    class FakeDataService:
        async def list_photometric_data(self, offset=0, count=100, filters=None):
            data = [
                PhotometricDataDto(
                    plugin_id=plugin_id,
                    julian_date=2450000.5,
                    magnitude=12.3,
                    magnitude_error=0.01,
                    light_filter="V",
                ),
                PhotometricDataDto(
                    plugin_id=plugin_id,
                    julian_date=2450001.5,
                    magnitude=12.4,
                    magnitude_error=0.02,
                    light_filter=None,
                ),
            ]

            return PaginationResponseDto[PhotometricDataDto](
                data=data,
                count=len(data),
                total_items=len(data),
            )

    return FakeDataService()


@pytest.fixture
def export_service(
    fake_export_repo, fake_plugin_service, fake_data_service_single_page
):
    return ExportService(
        export_repository=fake_export_repo,
        plugin_service=fake_plugin_service,
        data_service=fake_data_service_single_page,
    )


# ---------------------------------------------------------------------------
# build_task_set_key
# ---------------------------------------------------------------------------


def test_build_task_set_key_is_deterministic_and_order_independent():
    task_ids_1 = ["3", "1", "2"]
    task_ids_2 = ["2", "3", "1"]

    h1 = ExportService.build_task_set_key(task_ids_1, ExportOption.single_file)
    h2 = ExportService.build_task_set_key(task_ids_2, ExportOption.single_file)

    assert h1 == h2

    h3 = ExportService.build_task_set_key(task_ids_1, ExportOption.by_sources)
    assert h3 != h1


# ---------------------------------------------------------------------------
# _write_to_csv + _export_to_single_file
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_write_to_csv_writes_header_and_rows(
    export_service, fake_plugin_service, override_directories
):
    plugin_dict = {p.id: p.name for p in fake_plugin_service.plugins}
    csv_file = settings.TEMP_DIR / "test.csv"
    filters = Filters(filters={"task_id__in": ["t1", "t2"]})

    await export_service._write_to_csv(filters, plugin_dict, csv_file, ",")

    assert csv_file.exists()

    async with aiofiles.open(csv_file, "r") as f:
        content = await f.read()

    lines = content.strip().splitlines()
    # header + 2 rows from fake_data_service_single_page
    assert len(lines) == 3
    assert lines[0] == "JulianDate,Magnitude,MagnitudeError,LightFilter,SourceName"
    assert "SourceA" in lines[1]


@pytest.mark.asyncio
async def test_export_to_single_file_calls_write_to_csv(
    export_service, fake_plugin_service, override_directories, monkeypatch
):
    plugin_dict = {p.id: p.name for p in fake_plugin_service.plugins}
    filters = Filters(filters={"task_id__in": ["t1", "t2"]})
    work_dir = settings.TEMP_DIR / "work"
    work_dir.mkdir()

    called = {}

    async def fake_write_to_csv(
        filters_arg, plugin_dict_arg, csv_file_arg, delimiter_arg
    ):
        called["filters"] = filters_arg
        called["plugin_dict"] = plugin_dict_arg
        called["csv_file"] = csv_file_arg
        called["delimiter"] = delimiter_arg

    monkeypatch.setattr(export_service, "_write_to_csv", fake_write_to_csv)

    await export_service._export_to_single_file(
        filters, plugin_dict, work_dir, delimiter=";"
    )

    assert called["filters"] is filters
    assert called["plugin_dict"] is plugin_dict
    assert called["csv_file"] == work_dir / "export.csv"
    assert called["delimiter"] == ";"


# ---------------------------------------------------------------------------
# _zip_dir
# ---------------------------------------------------------------------------


def test_zip_dir_creates_zip_with_contents(export_service, override_directories):
    src = settings.RESOURCES_DIR / "src"
    src.mkdir()
    (src / "a.txt").write_text("hello")
    sub = src / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("world")

    dest_zip = settings.TEMP_DIR / "out.zip"

    export_service._zip_dir(src, dest_zip)

    assert dest_zip.exists()

    with zipfile.ZipFile(dest_zip, "r") as zf:
        names = sorted(zf.namelist())

    assert f"{src.name}/a.txt" in names
    assert f"{src.name}/sub/b.txt" in names


# ---------------------------------------------------------------------------
# _get_export_filename_by_hash
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_export_filename_by_hash_returns_none_when_not_found(
    export_service, fake_export_repo
):
    fake_export_repo.find_result = (0, [])
    result = await export_service._get_export_filename_by_hash("abc")
    assert result is None


@pytest.mark.asyncio
async def test_get_export_filename_by_hash_returns_filename_when_found(
    export_service, fake_export_repo
):
    ef = ExportFile(
        file_name="existing.zip",
        export_option=ExportOption.single_file,
        task_set_hash="abc",
    )
    fake_export_repo.find_result = (1, [ef])

    result = await export_service._get_export_filename_by_hash("abc")
    assert result == "existing.zip"


# ---------------------------------------------------------------------------
# export_data: existing archive case
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_data_returns_existing_filename_when_present(
    export_service, fake_export_repo, monkeypatch
):
    async def fake_get_export_filename(task_set_hash: str):
        return "existing.zip"

    monkeypatch.setattr(
        export_service, "_get_export_filename_by_hash", fake_get_export_filename
    )
    export_service._zip_dir = MagicMock()
    fake_export_repo.save = AsyncMock()

    filters = Filters(filters={"task_id__in": ["t1", "t2"]})

    result = await export_service.export_data(filters, ExportOption.single_file)

    assert result == "existing.zip"
    export_service._zip_dir.assert_not_called()
    fake_export_repo.save.assert_not_called()


# ---------------------------------------------------------------------------
# export_data: new single-file export
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_export_data_creates_new_zip_and_db_record(
    export_service,
    fake_export_repo,
    override_directories,
    monkeypatch,
):
    async def fake_get_export_filename(task_set_hash: str):
        return None

    monkeypatch.setattr(
        export_service, "_get_export_filename_by_hash", fake_get_export_filename
    )

    filters = Filters(filters={"task_id__in": ["task1", "task2"]})

    result = await export_service.export_data(filters, ExportOption.single_file)

    assert isinstance(result, Path)
    assert result.exists()
    assert result.suffix == ".zip"
    assert result.parent == settings.TEMP_DIR

    assert len(fake_export_repo.saved) == 1
    saved = fake_export_repo.saved[0]
    assert isinstance(saved, ExportFile)
    assert saved.export_option == ExportOption.single_file
    assert saved.file_name == result.name

    expected_hash = ExportService.build_task_set_key(
        filters.filters["task_id__in"], ExportOption.single_file
    )
    assert saved.task_set_hash == expected_hash
