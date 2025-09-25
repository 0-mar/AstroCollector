from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, HTTPException
from starlette import status
from starlette.responses import Response, FileResponse

from src.core.config.config import settings
from src.core.schemas import PaginationResponseDto
from src.core.security.auth import required_roles
from src.core.security.models import User
from src.core.security.schemas import UserRoleEnum
from src.plugin.schemas import PluginDto, CreatePluginDto, UpdatePluginDto
from src.plugin.service import PluginService, PLUGIN_DIR

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
    filters: dict[str, Any] | None = None,
) -> PaginationResponseDto[PluginDto]:
    """List plugins."""
    if filters is None:
        filters = {}
    plugins = await service.list_plugins(offset=offset, count=count, **filters)
    return plugins


@router.get("/download/{plugin_id}")
async def download_plugin(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    service: PluginServiceDep,
    plugin_id: UUID,
):
    plugin = await service.get_plugin(plugin_id)
    if plugin.file_name is None:
        raise HTTPException(status_code=404, detail="Plugin file does not exist")

    plugin_file_path = Path.joinpath(PLUGIN_DIR, plugin.file_name).resolve()
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


@router.delete("/{plugin_id}")
async def delete_plugin(
    _: Annotated[User, Depends(required_roles(UserRoleEnum.super_admin))],
    plugin_id: UUID,
    service: PluginServiceDep,
):
    """Delete plugin"""
    await service.delete_plugin(plugin_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
