import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest

from src.core.config.config import settings
from src.plugin.interface.catalog_plugin import CatalogPlugin
from src.plugin.model import Plugin
from src.tasks.service import SyncTaskService
from tests.default_test_plugins.plugin_test import plugin


class TestTaskService:
    @pytest.fixture
    def sync_task_service(self) -> SyncTaskService:
        session = Mock()

        return SyncTaskService(session, None)

    @pytest.fixture
    def plugin_entity(self) -> Plugin:
        return Plugin(
            id=uuid.UUID("abb15bc1-4926-497d-b337-0a7d529b62f1"),
            catalog_url="https://google.com",
            description="hey",
            created_by="test",
            directly_identifies_objects=True,
            file_name="abb15bc1-4926-497d-b337-0a7d529b62f1.py",
            name="Test",
            created=datetime(2025, 9, 29),
        )

    @pytest.fixture
    def create_plugin_script(self):
        plugin_script = settings.PLUGIN_DIR / "abb15bc1-4926-497d-b337-0a7d529b62f1.py"

        with open(plugin_script, "wb") as out_file:
            with open(plugin.__file__, "rb") as in_file:
                while content := in_file.read(1024):
                    out_file.write(content)

    def test_load_plugin(
        self,
        override_directories,
        plugin_entity,
        create_plugin_script,
        sync_task_service,
    ):
        instance = sync_task_service._load_plugin(
            "abb15bc1-4926-497d-b337-0a7d529b62f1.py",
            settings.PLUGIN_DIR / "abb15bc1-4926-497d-b337-0a7d529b62f1.py",
        )
        assert isinstance(instance, CatalogPlugin)
        assert type(instance).__name__ == "PluginTest"
