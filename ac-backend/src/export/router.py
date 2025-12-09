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
    """
    Handles the export functionality of data based on provided parameters (export option and delimiter).
    Streams the resulting exported data back to the client as a ZIP file.

    :param export_service: The service responsible for handling
        data export operations.
    :type export_service: ExportServiceDep
    :param export_option: The export option
    :type export_option: ExportOption
    :param filters: The criteria and constraints to filter data for the export operation.
        Requires `task_id__in` to be included in the filters.
    :type filters: Filters
    :param delimiter: The delimiter used for splitting the exported data columns. Defaults to a comma.
    :type delimiter: str
    :return: A streaming response consisting of the exported ZIP file
    :rtype: StreamingResponse
    :raises APIException: If the required 'task_id__in' is not provided in the filter criteria.

    """
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
