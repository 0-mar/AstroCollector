from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from fastapi.openapi.models import Response

from src.plugin.plugin_schemas import PluginDto, CreatePluginDto
from src.plugin.plugin_service import PluginService, get_plugin_service

PluginServiceDep = Annotated[PluginService, Depends(PluginService)]

PLUGIN_DIR = Path(__file__).parent.parent.parent

router = APIRouter(
    prefix="/api/plugins",
    tags=["plugins"],
    responses={404: {"description": "Not found"}}
)

@router.get("/{plugin_id}", response_model=PluginDto)
async def get_plugin(
    plugin_id: str,
    service: PluginServiceDep,
) -> PluginDto:
    """Get plugin by ID."""
    plugin = await service.get_plugin(plugin_id)
    return plugin


@router.post("", response_model=PluginDto)
async def create_plugin(
    create_dto: CreatePluginDto,
    service: PluginServiceDep,) -> PluginDto:
    """Create plugin"""

    plugin = await service.create_plugin(create_dto)

    return plugin



@router.put("/upload/{plugin_id}")
async def upload_plugin(
    plugin_id: str,
    plugin_file: UploadFile,
    service: PluginServiceDep,) -> None:
    """Upload plugin"""

    await service.upload_plugin(plugin_id, plugin_file)


@router.post("/run/{plugin_id}")
async def run_plugin(
    plugin_id: str,
    service: PluginServiceDep,) -> None:
    """Run plugin"""

    return await service.run_plugin(plugin_id, 290.925, 38.961, 60)