import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Optional, Any
from uuid import UUID

from sqlalchemy import insert, update
from sqlalchemy.orm import Session

from src.core.config.config import settings
from src.plugin.interface.catalog_plugin import CatalogPlugin, DefaultCatalogPlugin
from src.plugin.interface.schemas import StellarObjectIdentificatorDto
from src.core.repository.exception import RepositoryException

from src.plugin.exceptions import NoPluginClassException
from src.plugin.model import Plugin
from src.tasks.model import Task
from src.tasks.types import TaskStatus

logger = logging.getLogger(__name__)


class SyncTaskService:
    def __init__(self, session: Session, model) -> None:
        self._session = session
        self._model = model

    def _get_plugin_entity(self, entity_id: UUID) -> Plugin:
        result = self._session.get(Plugin, entity_id)
        self._session.commit()
        if result is None:
            raise RepositoryException("Plugin with ID " + str(entity_id) + " not found")
        return result

    def _load_plugin(
        self, module_name: str, file_path: Path
    ) -> Optional[CatalogPlugin[StellarObjectIdentificatorDto]]:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            raise ImportError(f"Could not load spec from {file_path}")
        plugin_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = plugin_module
        if spec.loader is None:
            raise ImportError(f"Could not load loader from {file_path}")
        spec.loader.exec_module(plugin_module)

        clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
        for _, cls in clsmembers:
            # Only add classes that are a sub class of PhotometricCataloguePlugin,
            # but NOT PhotometricCataloguePlugin itself
            if (
                issubclass(cls, CatalogPlugin)
                and cls is not CatalogPlugin
                and cls is not DefaultCatalogPlugin
            ):
                logger.info(f"Found plugin class: {cls.__module__}.{cls.__name__}")
                return cls()

        return None

    def get_plugin_instance(
        self, plugin_id: UUID
    ) -> CatalogPlugin[StellarObjectIdentificatorDto]:
        db_plugin = self._get_plugin_entity(plugin_id)
        plugin_file_path = Path.joinpath(
            settings.PLUGIN_DIR, db_plugin.file_name
        ).resolve()

        plugin = self._load_plugin(db_plugin.file_name, plugin_file_path)
        if plugin is None:
            raise NoPluginClassException()

        return plugin

    def bulk_insert(self, data: list[dict[Any, Any]]):
        if data == []:
            return
        self._session.execute(insert(self._model), data)
        self._session.commit()

    def set_task_status(self, task_id: str, status: TaskStatus):
        uuid = UUID(task_id)
        stmt = update(Task).where(Task.id == uuid).values(status=status)
        self._session.execute(stmt)
        self._session.commit()
