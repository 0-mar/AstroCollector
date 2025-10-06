import importlib
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Optional
from uuid import UUID

from src.core.config.config import settings
from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import StellarObjectIdentificatorDto
from src.core.repository.exception import RepositoryException
from src.default_plugins.mast.mast_plugin import MastPlugin
from src.plugin.exceptions import NoPluginClassException
from src.plugin.model import Plugin

logger = logging.getLogger(__name__)


class SyncTaskService:
    def __init__(self, session, model):
        self._session = session
        self._model = model

    def _get(self, entity_id: UUID) -> Plugin:
        result = self._session.get(Plugin, entity_id)
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
                and cls is not MastPlugin
            ):
                logger.info(f"Found plugin class: {cls.__module__}.{cls.__name__}")
                return cls()

        return None

    def get_plugin_instance(
        self, plugin_id: UUID
    ) -> CatalogPlugin[StellarObjectIdentificatorDto]:
        db_plugin = self._session.get(Plugin, plugin_id)
        plugin_file_path = Path.joinpath(
            settings.PLUGIN_DIR, db_plugin.file_name
        ).resolve()

        plugin = self._load_plugin(db_plugin.file_name, plugin_file_path)
        if plugin is None:
            raise NoPluginClassException()

        return plugin
