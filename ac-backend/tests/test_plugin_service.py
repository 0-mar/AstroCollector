import io
import os
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock

import pytest
from fastapi import UploadFile

from src.core.config.config import settings
from src.plugin import service
from src.plugin.model import Plugin
from src.plugin.schemas import CreatePluginDto, PluginDto
from src.plugin.service import PluginService
from tests import conftest, default_test_plugins
from tests.default_test_plugins.plugin_test import plugin
from tests.default_test_plugins.plugin_test.plugin import PluginTest


class TestPluginService:
    @pytest.fixture
    def plugin_entity(self) -> Plugin:
        return Plugin(
            id=uuid.UUID("abb15bc1-4926-497d-b337-0a7d529b62f1"),
            catalog_url="https://google.com",
            description="Test plugin",
            created_by="system",
            directly_identifies_objects=True,
            file_name="mock.py",
            name="Test",
            created=datetime(2025, 9, 29),
        )

    @pytest.fixture
    def create_plugin_file(self) -> None:
        with open(settings.PLUGIN_DIR / "mock.py", "w") as f:
            f.write("print('hello from plugin')\n")

    @pytest.fixture
    def mock_repository(self, plugin_entity):
        repo = Mock()
        repo.save = AsyncMock(return_value=plugin_entity)
        repo.get = AsyncMock(return_value=plugin_entity)

        # async update: capture file_name from update_data and put it on entity
        async def update_side_effect(plugin_id, update_data: dict):
            assert plugin_id == plugin_entity.id
            assert "file_name" in update_data
            plugin_entity.file_name = update_data["file_name"]
            return plugin_entity

        repo.update = AsyncMock(side_effect=update_side_effect)
        repo.delete = AsyncMock(return_value=None)

        return repo

    @pytest.fixture
    def plugin_service(self, mock_repository):
        return PluginService(mock_repository)

    @pytest.mark.asyncio
    async def test_create_plugin(
        self, override_directories, plugin_service, plugin_entity
    ):
        """Test plugin creation through service."""
        create_dto = CreatePluginDto(
            name="Test",
            catalog_url="mock",
            description="hey",
            directly_identifies_objects=True,
            created_by="test",
        )

        result = await plugin_service.create_plugin(create_dto)

        assert result.created == plugin_entity.created
        assert result.created_by == plugin_entity.created_by
        assert result.description == plugin_entity.description
        assert (
            result.directly_identifies_objects
            == plugin_entity.directly_identifies_objects
        )
        assert result.file_name == plugin_entity.file_name
        assert result.name == plugin_entity.name
        assert Path.joinpath(settings.RESOURCES_DIR, str(plugin_entity.id)).exists()

    @pytest.mark.asyncio
    async def test_upload_plugin(
        self, override_directories, plugin_service, plugin_entity, create_plugin_file
    ):
        # create an UploadFile with some content
        file_bytes = b"print('hello from plugin')\n"
        upload_file = UploadFile(
            filename="test_plugin_service.py",
            file=io.BytesIO(file_bytes),
        )
        print(Path.joinpath(settings.RESOURCES_DIR, str(plugin_entity.id)))
        result: PluginDto = await plugin_service.upload_plugin(
            plugin_entity.id, upload_file
        )

        assert result.id == plugin_entity.id

        # file was created in PLUGIN_DIR with the expected name
        assert result.file_name is not None
        written_file_path = settings.PLUGIN_DIR / result.file_name
        assert written_file_path.exists(), "Plugin file was not created on disk"

        # check content
        assert written_file_path.read_bytes() == file_bytes

    @pytest.mark.asyncio
    async def test_delete_plugin(
        self, override_directories, plugin_service, plugin_entity, create_plugin_file
    ):
        os.mkdir(settings.RESOURCES_DIR / str(plugin_entity.id))

        await plugin_service.delete_plugin(plugin_entity.id)
        assert not Path.joinpath(settings.PLUGIN_DIR, plugin_entity.file_name).exists()

    @pytest.mark.asyncio
    async def test_register_plugins(self, override_directories, plugin_service):
        dto: PluginDto = await plugin_service._PluginService__register_plugin(plugin)
        test_plugin = PluginTest()
        print(dto.catalog_url)
        print(test_plugin.catalog_url)
        # plugin dir contains the plugin file
        assert len([file for file in settings.PLUGIN_DIR.iterdir()]) == 1

        assert dto.name == test_plugin.catalog_name
        assert dto.catalog_url == test_plugin.catalog_url
        assert (
            dto.directly_identifies_objects == test_plugin.directly_identifies_objects
        )
        assert dto.description == test_plugin.description
        assert dto.created_by == "system"

    @pytest.mark.asyncio
    async def test_register_plugins_no_plugin_class(
        self, override_directories, plugin_service
    ):
        with pytest.raises(NotImplementedError):
            await plugin_service._PluginService__register_plugin(conftest)

    @pytest.mark.asyncio
    async def test_create_default_plugins(
        self, monkeypatch, override_directories, plugin_service
    ):
        # override the symbol used by create_default_plugins
        monkeypatch.setattr(service, "default_plugins", default_test_plugins)
        print(service.default_plugins.__path__)
        print(settings.RESOURCES_DIR)
        await plugin_service.create_default_plugins()
        assert len([dir for dir in settings.RESOURCES_DIR.iterdir()]) == 1
