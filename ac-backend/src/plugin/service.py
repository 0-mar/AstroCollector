# https://docs.python.org/3/library/importlib.html
import importlib.util
import inspect
import os
import shutil
import uuid
from uuid import UUID
from collections.abc import Iterator
from pathlib import Path
import logging

import importlib
import pkgutil
from types import ModuleType
from typing import Annotated

from fastapi import Depends, UploadFile
import aiofiles
from fastapi.concurrency import run_in_threadpool

from src import default_plugins
from src.core.config.config import settings
from src.core.integration.catalog_plugin import CatalogPlugin
from src.core.integration.schemas import StellarObjectIdentificatorDto
from src.core.repository.repository import Repository, get_repository, Filters
from src.core.schemas import PaginationResponseDto

from src.plugin.model import Plugin
from src.plugin.schemas import (
    PluginDto,
    CreatePluginDto,
    UpdatePluginDto,
    UpdatePluginFileDto,
)

PluginRepositoryDep = Annotated[Repository[Plugin], Depends(get_repository(Plugin))]

# What about plugin cache?
# https://stackoverflow.com/questions/65041691/is-python-dictionary-async-safe

logger = logging.getLogger(__name__)


class PluginService:
    def __init__(self, repository: PluginRepositoryDep):
        self._repository = repository
        self.plugins: dict[str, CatalogPlugin[StellarObjectIdentificatorDto]] = dict()

    async def get_plugin(self, plugin_id: UUID) -> PluginDto:
        plugin = await self._repository.get(plugin_id)
        return PluginDto.model_validate(plugin)

    async def create_plugin(self, create_dto: CreatePluginDto) -> PluginDto:
        dto_data = create_dto.model_dump()
        plugin = Plugin(**dto_data, file_name=None)

        plugin = await self._repository.save(plugin)
        # make resources directory for the plugin
        await run_in_threadpool(os.mkdir, settings.RESOURCES_DIR / str(plugin.id))

        return PluginDto.model_validate(plugin)

    async def update_plugin(self, update_dto: UpdatePluginDto) -> PluginDto:
        # check if exists
        await self.get_plugin(update_dto.id)

        update_data = update_dto.model_dump(exclude_none=True)
        plugin = await self._repository.update(update_dto.id, update_data)
        return PluginDto.model_validate(plugin)

    async def upload_plugin(
        self, plugin_id: UUID, plugin_file: UploadFile
    ) -> PluginDto:
        plugin_entity: Plugin = await self._repository.get(plugin_id)  # check if exists

        # delete old file if exists
        if plugin_entity.file_name is not None:
            old_file_path = Path.joinpath(
                settings.PLUGIN_DIR, plugin_entity.file_name
            ).resolve()
            await run_in_threadpool(old_file_path.unlink)

        new_file_name = str(uuid.uuid4()) + ".py"

        plugin_file_path = Path.joinpath(settings.PLUGIN_DIR, new_file_name).resolve()
        async with aiofiles.open(plugin_file_path, "wb") as out_file:
            while content := await plugin_file.read(1024):  # async read chunk
                await out_file.write(content)  # async write chunk

        update_data = UpdatePluginFileDto(id=plugin_entity.id, file_name=new_file_name)
        plugin = await self._repository.update(plugin_id, update_data.model_dump())
        return PluginDto.model_validate(plugin)

    async def delete_plugin(self, plugin_id: UUID) -> None:
        plugin = await self._repository.get(plugin_id)
        if plugin.file_name is not None:
            plugin_file_path = Path.joinpath(
                settings.PLUGIN_DIR, plugin.file_name
            ).resolve()
            await run_in_threadpool(plugin_file_path.unlink)

        # delete resources directory of the plugin
        await run_in_threadpool(shutil.rmtree, settings.RESOURCES_DIR / str(plugin.id))

        await self._repository.delete(plugin_id)

    async def list_plugins(
        self,
        offset: int = 0,
        count: int = settings.MAX_PAGINATION_BATCH_COUNT,
        filters: Filters | None = None,
    ) -> PaginationResponseDto[PluginDto]:
        total_count, plugin_list = await self._repository.find(
            offset=offset, count=count, filters=filters
        )
        data = list(map(PluginDto.model_validate, plugin_list))
        return PaginationResponseDto[PluginDto](
            data=data, count=len(data), total_items=total_count
        )

    async def list_resources(self, plugin_id: UUID) -> list[str]:
        # check if exists
        await self._repository.get(plugin_id)
        plugin_resources_dir = settings.RESOURCES_DIR / str(plugin_id)

        return os.listdir(plugin_resources_dir)

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
                issubclass(cls, CatalogPlugin) and cls is not CatalogPlugin
                #                and cls is not MastPlugin
            ):
                logger.info(
                    f"Found default plugin class: {cls.__module__}.{cls.__name__}"
                )

                plugin_instance: CatalogPlugin = cls()

                dto = await self.create_plugin(
                    CreatePluginDto(
                        name=plugin_instance.catalog_name,
                        created_by="system",
                        directly_identifies_objects=plugin_instance.directly_identifies_objects,
                        description=plugin_instance.description,
                        catalog_url=plugin_instance.catalog_url,
                    )
                )

                new_file_name = str(uuid.uuid4()) + ".py"
                plugin_file_path = Path.joinpath(
                    settings.PLUGIN_DIR, new_file_name
                ).resolve()
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
