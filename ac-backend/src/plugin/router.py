import os
from pathlib import Path
from typing import Annotated
from uuid import UUID

import aiofiles
from fastapi import APIRouter, Depends, UploadFile, HTTPException, Request
from starlette import status
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response, FileResponse
from datetime import datetime

from src.core.config.config import settings
from src.core.repository.repository import Filters
from src.core.service.schemas import PaginationResponseDto
from src.core.security.auth import required_roles
from src.core.security.models import User
from src.core.security.schemas import UserRoleEnum
from src.plugin.schemas import PluginDto, CreatePluginDto, UpdatePluginDto
from src.plugin.service import PluginService
from src.plugin.utils import unzip_archive

PluginServiceDep = Annotated[PluginService, Depends(PluginService)]

router = APIRouter(
    prefix="/api/plugins",
    tags=["plugins"],
    responses={404: {"description": "Not found"}},
)


@router.post("/list")
async def list_plugins(
    service: PluginServiceDep,
    offset: int = 0,
    count: int = settings.MAX_PAGINATION_BATCH_COUNT,
    filters: Filters | None = None,
) -> PaginationResponseDto[PluginDto]:
    """List plugins."""
    plugins = await service.list_plugins(offset=offset, count=count, filters=filters)
    return plugins


@router.get("/download/{plugin_id}")
async def download_plugin(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    service: PluginServiceDep,
    plugin_id: UUID,
):
    """
    Handles the downloading of a plugin file by its plugin UUID.

    :param _: The authenticated user with the necessary role (`super_admin`). This
              parameter ensures the user has access permissions for the operation.
    :param service: Plugin service dependency.
    :param plugin_id: UUID of the plugin to be downloaded. Used to fetch the plugin's
                      details and verify its file presence.
    :return: A `FileResponse` object containing the plugin file
    """
    plugin = await service.get_plugin(plugin_id)
    if plugin.file_name is None:
        raise HTTPException(status_code=404, detail="Plugin file does not exist")

    plugin_file_path = Path.joinpath(settings.PLUGIN_DIR, plugin.file_name).resolve()
    return FileResponse(
        plugin_file_path,
        media_type="text/x-python; charset=utf-8",
        filename=f"{plugin.name}.py",
    )


@router.get("/{plugin_id}", response_model=PluginDto)
async def get_plugin(
    plugin_id: UUID,
    service: PluginServiceDep,
) -> PluginDto:
    """Get plugin by ID."""
    plugin = await service.get_plugin(plugin_id)
    return plugin


@router.post("", response_model=PluginDto)
async def create_plugin(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    create_dto: CreatePluginDto,
    service: PluginServiceDep,
) -> PluginDto:
    """Create plugin"""

    plugin = await service.create_plugin(create_dto)

    return plugin


@router.put("/{plugin_id}", response_model=PluginDto)
async def update_plugin(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    update_dto: UpdatePluginDto,
    plugin_id: UUID,
    service: PluginServiceDep,
) -> PluginDto:
    """Update plugin"""

    update_dto.id = plugin_id
    plugin = await service.update_plugin(update_dto)

    return plugin


@router.put("/upload/{plugin_id}")
async def upload_plugin(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    plugin_id: UUID,
    plugin_file: UploadFile,
    service: PluginServiceDep,
) -> PluginDto:
    """Upload plugin source code file"""
    return await service.upload_plugin(plugin_id, plugin_file)


@router.put("/upload-resources/{plugin_id}")
async def upload_resources(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    plugin_id: UUID,
    service: PluginServiceDep,
    request: Request,
):
    """
    Upload resources as a zip archive for the corresponding plugin.
    """
    # check if plugin exists
    await service.get_plugin(plugin_id)

    filename = f"data_{datetime.now().strftime('%d_%m_%Y_%H_%M')}.zip"
    plugin_resources_dir = settings.RESOURCES_DIR / str(plugin_id)
    archive_path = plugin_resources_dir / filename
    async with aiofiles.open(archive_path, "wb") as f:
        async for chunk in request.stream():
            await f.write(chunk)

    # unzip archive
    await run_in_threadpool(unzip_archive, archive_path, plugin_resources_dir)
    # delete archive file
    os.unlink(archive_path)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/resources/{plugin_id}")
async def list_resources(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    plugin_id: UUID,
    service: PluginServiceDep,
):
    """
    Fetch a list of resources associated with a specific plugin.
    """
    resources = await service.list_resources(plugin_id)
    return {"resources": resources}


@router.delete("/{plugin_id}")
async def delete_plugin(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    plugin_id: UUID,
    service: PluginServiceDep,
):
    """Delete plugin"""
    await service.delete_plugin(plugin_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
