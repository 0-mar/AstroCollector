import zipfile
from io import StringIO
from pathlib import Path

import aiofiles
from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse

from src.core.config.config import settings
from src.core.exception.exceptions import APIException
from src.core.repository.repository import Filters
from src.data_retrieval.router import DataServiceDep
from src.plugin.router import PluginServiceDep

router = APIRouter(
    prefix="/api/export",
    tags=["so-name-resolving"],
    responses={404: {"description": "Not found"}},
)


@router.post("/csv")
async def photometric_data_to_csv(
    data_service: DataServiceDep,
    plugin_service: PluginServiceDep,
    delimiter: str = ",",
    filters: Filters | None = None,
):
    if (
        filters is None
        or filters.filters is None
        or (
            "task_id__eq" not in filters.filters
            and "task_id__in" not in filters.filters
        )
    ):
        raise APIException("task_id__eq or task_id__in required in filters")

    plugins = await plugin_service.list_plugins()
    plugin_dict = {dto.id: dto.name for dto in plugins.data}

    async def csv_chunk():
        count = settings.MAX_PAGINATION_BATCH_COUNT
        offset = 0
        builder = StringIO()
        # write header
        builder.write("JulianDate,Magnitude,MagnitudeError,LightFilter,SourceName\n")

        while True:
            page = await data_service.list_photometric_data(
                offset=offset, count=count, filters=filters
            )
            offset += page.count

            for record in page.data:
                source_name = plugin_dict[record.plugin_id]
                builder.write(
                    f"{record.julian_date}{delimiter}{record.magnitude}{delimiter}{record.magnitude_error}{delimiter}{record.light_filter if record.light_filter is not None else ''}{delimiter}{source_name}\n"
                )

            yield builder.getvalue()
            builder = StringIO()
            if offset >= page.total_items:
                break

    return StreamingResponse(
        csv_chunk(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"},
    )


def create_zip(zip_filename: Path, filters: Filters) -> None:
    with zipfile.ZipFile(zip_filename, "w") as zip_file:
        for task_id in filters.filters["task_id__in"]:
            filename = f"{task_id}.csv"
            zip_file.write(
                Path.joinpath(settings.TEMP_DIR, filename).resolve(),
                filename,
                compress_type=zipfile.ZIP_DEFLATED,
            )


@router.post("/raw")
async def get_raw_photometric_data(
    filters: Filters | None = None,
):
    if (
        filters is None
        or filters.filters is None
        and "task_id__in" not in filters.filters
    ):
        raise APIException("task_id__in required in filters")

    zip_filename = Path.joinpath(
        settings.TEMP_DIR, f"{filters.filters['task_id__in'][0]}.zip"
    ).resolve()

    await run_in_threadpool(create_zip, zip_filename, filters)

    async def iter_file(path, chunk_size=1024 * 1024):
        async with aiofiles.open(path, "rb") as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(
        iter_file(zip_filename),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=raw_data.zip"},
    )
