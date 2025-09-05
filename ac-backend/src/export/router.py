import io
from typing import Any

from fastapi import APIRouter
from starlette.responses import StreamingResponse

from src.core.config.config import settings
from src.core.exception.exceptions import APIException
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
    filters: dict[str, Any] | None = None,
):
    if filters is None or (
        "task_id__eq" not in filters and "task_id__in" not in filters
    ):
        raise APIException("task_id__eq or task_id__in required in filters")

    plugins = await plugin_service.list_plugins()
    plugin_dict = {dto.id: dto.name for dto in plugins.data}

    async def csv_chunk():
        count = settings.MAX_PAGINATION_BATCH_COUNT
        offset = 0
        builder = io.StringIO()
        # write header
        builder.write("JulianDate,Magnitude,MagnitudeError,LightFilter,SourceName\n")

        while True:
            page = await data_service.list_photometric_data(
                offset=offset, count=count, **filters
            )
            offset += page.count

            for record in page.data:
                source_name = plugin_dict[record.plugin_id]
                builder.write(
                    f"{record.julian_date}{delimiter}{record.magnitude}{delimiter}{record.magnitude_error}{delimiter}{record.light_filter if record.light_filter is not None else ''}{delimiter}{source_name}\n"
                )

            yield builder.getvalue()
            builder = io.StringIO()
            if offset >= page.total_items:
                break

    return StreamingResponse(
        csv_chunk(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"},
    )
