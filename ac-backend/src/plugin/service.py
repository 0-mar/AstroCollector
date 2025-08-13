# https://docs.python.org/3/library/importlib.html
import importlib.util
import inspect
import sys
import uuid
from uuid import UUID
from collections.abc import Iterator
from pathlib import Path
import logging

import importlib
import pkgutil
from types import ModuleType
from typing import Annotated, Optional, Any

from fastapi import Depends, UploadFile
import aiofiles
from fastapi.concurrency import run_in_threadpool

from src import default_plugins
from src.core.integration.photometric_catalogue_plugin import PhotometricCataloguePlugin
from src.core.integration.schemas import StellarObjectIdentificatorDto
from src.core.repository.repository import Repository, get_repository, LIMIT
from src.core.schemas import PaginationResponseDto
from src.default_plugins.mast.mast_plugin import MastPlugin
from src.plugin.exceptions import NoPluginClassException
from src.plugin.model import Plugin
from src.plugin.schemas import (
    PluginDto,
    CreatePluginDto,
    UpdatePluginDto,
    UpdatePluginFileDto,
)

PluginRepositoryDep = Annotated[Repository[Plugin], Depends(get_repository(Plugin))]
PLUGIN_DIR = Path.joinpath(Path(__file__).parent.parent.parent, "plugins").resolve()

# What about plugin cache?
# https://stackoverflow.com/questions/65041691/is-python-dictionary-async-safe

logger = logging.getLogger(__name__)


class PluginService:
    def __init__(self, repository: PluginRepositoryDep):
        self._repository = repository
        self.plugins: dict[
            str, PhotometricCataloguePlugin[StellarObjectIdentificatorDto]
        ] = dict()

    def _load_plugin(
        self, module_name: str, file_path: Path
    ) -> Optional[PhotometricCataloguePlugin[StellarObjectIdentificatorDto]]:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            logger.error(f"Could not load spec from {file_path}")
            raise ImportError(f"Could not load spec from {file_path}")
        plugin_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = plugin_module
        if spec.loader is None:
            logger.error(f"Could not load loader from {file_path}")
            raise ImportError(f"Could not load loader from {file_path}")
        spec.loader.exec_module(plugin_module)

        clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
        for _, cls in clsmembers:
            # Only add classes that are a sub class of PhotometricCataloguePlugin,
            # but NOT PhotometricCataloguePlugin itself
            if (
                issubclass(cls, PhotometricCataloguePlugin)
                and cls is not PhotometricCataloguePlugin
                and cls is not MastPlugin
            ):
                logger.info(f"Found plugin class: {cls.__module__}.{cls.__name__}")
                return cls()

        return None

    async def get_plugin(self, plugin_id: UUID) -> PluginDto:
        plugin = await self._repository.get(plugin_id)
        return PluginDto.model_validate(plugin)

    async def create_plugin(self, create_dto: CreatePluginDto) -> PluginDto:
        dto_data = create_dto.model_dump()
        plugin = Plugin(**dto_data, file_name=None)

        plugin = await self._repository.save(plugin)
        return PluginDto.model_validate(plugin)

    async def update_plugin(self, update_dto: UpdatePluginDto) -> PluginDto:
        # check if exists
        await self.get_plugin(update_dto.id)

        update_data = update_dto.model_dump(exclude_none=True)
        plugin = await self._repository.update(update_dto.id, update_data)
        return PluginDto.model_validate(plugin)

    async def upload_plugin(self, plugin_id: UUID, plugin_file: UploadFile) -> None:
        plugin_entity: Plugin = await self._repository.get(plugin_id)  # check if exists

        new_file_name = str(uuid.uuid4()) + ".py"
        plugin_file_path = Path.joinpath(PLUGIN_DIR, new_file_name).resolve()
        async with aiofiles.open(plugin_file_path, "wb") as out_file:
            while content := await plugin_file.read(1024):  # async read chunk
                await out_file.write(content)  # async write chunk

        update_data = UpdatePluginFileDto(id=plugin_entity.id, file_name=new_file_name)
        await self._repository.update(plugin_id, update_data.model_dump())

    async def delete_plugin(self, plugin_id: UUID) -> None:
        plugin = await self._repository.get(plugin_id)
        plugin_file_path = Path.joinpath(PLUGIN_DIR, plugin.file_name).resolve()
        await run_in_threadpool(plugin_file_path.unlink)
        await self._repository.delete(plugin_id)

    async def list_plugins(
        self, offset: int = 0, count: int = LIMIT, **kwargs: dict[str, Any]
    ) -> PaginationResponseDto[PluginDto]:
        total_count, plugin_list = await self._repository.find(
            offset=offset, count=count, **kwargs
        )
        data = list(map(PluginDto.model_validate, plugin_list))
        return PaginationResponseDto[PluginDto](
            data=data, count=len(data), total_items=total_count
        )

    async def get_plugin_instance(
        self, plugin_id: UUID
    ) -> PhotometricCataloguePlugin[StellarObjectIdentificatorDto]:
        db_plugin = await self._repository.get(plugin_id)
        plugin_file_path = Path.joinpath(PLUGIN_DIR, db_plugin.file_name).resolve()

        plugin = await run_in_threadpool(
            self._load_plugin, db_plugin.file_name, plugin_file_path
        )
        if plugin is None:
            raise NoPluginClassException()

        return plugin

    async def create_default_plugins(self):
        # https://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures
        # https://mwax911.medium.com/building-a-plugin-architecture-with-python-7b4ab39ad4fc
        # https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/
        # https://www.guidodiepen.nl/2019/02/implementing-a-simple-plugin-framework-in-python/

        # iterate over all .py files
        # for plugin_file_path in self.plugin_path_dir.rglob('*.py'):
        #     # because path is object not string
        #     path_in_str = str(plugin_file_path)
        #
        #     self.import_from_path(path_in_str)

        # self.discovered_plugins = {
        #     name: importlib.import_module(name)
        #     for finder, name, ispkg
        #     in self.iter_namespace(plugins)
        # }

        for finder, name, ispkg in self.__iter_namespace(default_plugins):
            plugin_module: ModuleType = importlib.import_module(name)
            if ispkg:
                for _, plugin_name, _ in self.__iter_namespace(plugin_module):
                    plugin_mod: ModuleType = importlib.import_module(plugin_name)
                    await self.__register_plugin(plugin_mod)

    async def __register_plugin(self, plugin_module: ModuleType) -> None:
        clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
        for _, cls in clsmembers:
            # Only add classes that are a sub class of PhotometricCataloguePlugin,
            # but NOT PhotometricCataloguePlugin itself
            if (
                issubclass(cls, PhotometricCataloguePlugin)
                and cls is not PhotometricCataloguePlugin
                and cls is not MastPlugin
            ):
                logger.info(
                    f"Found default plugin class: {cls.__module__}.{cls.__name__}"
                )
                dto = await self.create_plugin(
                    CreatePluginDto(
                        name=cls.__name__[: cls.__name__.rfind("Plugin")],
                        created_by="system",
                    )
                )

                new_file_name = str(uuid.uuid4()) + ".py"
                plugin_file_path = Path.joinpath(PLUGIN_DIR, new_file_name).resolve()
                async with aiofiles.open(plugin_file_path, "wb") as out_file:
                    async with aiofiles.open(plugin_module.__file__, "rb") as in_file:
                        while content := await in_file.read(1024):
                            await out_file.write(content)

                update_data = UpdatePluginFileDto(id=dto.id, file_name=new_file_name)
                await self._repository.update(dto.id, update_data.model_dump())

    def __iter_namespace(self, ns_pkg: ModuleType) -> Iterator[pkgutil.ModuleInfo]:
        # Specifying the second argument (prefix) to iter_modules makes the
        # returned name an absolute name instead of a relative one. This allows
        # import_module to work without having to do additional modification to
        # the name.
        return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


def get_plugin_service(repository: PluginRepositoryDep) -> PluginService:
    """Dependency for getting plugin service instance."""
    return PluginService(repository)
