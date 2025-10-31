from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from src.core.config.config import settings
from src.core.exception.exceptions import APIException
from src.core.repository.repository import Filters
from src.export.service import ExportService
from src.export.types import ExportOption

ExportServiceDep = Annotated[ExportService, Depends(ExportService)]

router = APIRouter(
    prefix="/api/export",
    tags=["export"],
    responses={404: {"description": "Not found"}},
)


@router.post("")
async def export_data(
    export_service: ExportServiceDep,
    export_option: ExportOption,
    filters: Filters,
    delimiter: str = ",",
):
    if filters.filters is None or ("task_id__in" not in filters.filters):
        raise APIException("task_id__in required in filters")

    export_file = await export_service.export_data(filters, export_option, delimiter)

    async def iter_file(path, chunk_size=1024 * 1024):
        async with aiofiles.open(path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        iter_file(settings.TEMP_DIR / export_file),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=export.zip"},
    )
