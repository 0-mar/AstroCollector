import hashlib
import json
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import Annotated
from uuid import uuid4, UUID

import aiofiles
from fastapi import Depends
from starlette.concurrency import run_in_threadpool

from src.core.config.config import settings
from src.core.repository.repository import get_repository, Repository, Filters
from src.data_retrieval.router import DataServiceDep
from src.export.model import ExportFile
from src.export.types import ExportOption
from src.plugin.router import PluginServiceDep
from src.plugin.schemas import PluginDto

ExportRepositoryDep = Annotated[
    Repository[ExportFile], Depends(get_repository(ExportFile))
]

logger = logging.getLogger(__name__)


class ExportService:
    def __init__(
        self,
        export_repository: ExportRepositoryDep,
        plugin_service: PluginServiceDep,
        data_service: DataServiceDep,
    ):
        self._export_repository = export_repository
        self._plugin_service = plugin_service
        self._data_service = data_service

    async def _write_to_csv(
        self,
        filters: Filters,
        plugin_dict: dict[UUID, PluginDto],
        csv_file: Path,
        delimiter: str,
    ):
        count = settings.MAX_PAGINATION_BATCH_COUNT
        offset = 0

        async with aiofiles.open(csv_file, "w") as out_file:
            # write header
            await out_file.write(
                "JulianDate,Magnitude,MagnitudeError,LightFilter,SourceName\n"
            )

            while True:
                page = await self._data_service.list_photometric_data(
                    offset=offset, count=count, filters=filters
                )
                offset += page.count

                for record in page.data:
                    source_name = plugin_dict[record.plugin_id]
                    await out_file.write(
                        f"{record.julian_date}{delimiter}{record.magnitude}{delimiter}{record.magnitude_error}{delimiter}{record.light_filter if record.light_filter is not None else ''}{delimiter}{source_name}\n"
                    )

                if offset >= page.total_items:
                    break

    async def _export_to_single_file(
        self,
        filters: Filters,
        plugin_dict: dict[UUID, PluginDto],
        work_dir: Path,
        delimiter: str,
    ):
        csv_file = work_dir / "export.csv"
        await self._write_to_csv(filters, plugin_dict, csv_file, delimiter)

    async def _export_by_sources(self, filters, plugin_dict, work_dir, delimiter):
        task_ids = filters.filters["task_id__in"]
        groups: dict[str, list[str]] = {}

        # split tasks by sources
        for task_id in task_ids:
            page = await self._data_service.list_photometric_data(
                count=1, filters=Filters(filters={"task_id__eq": task_id})
            )
            if page.total_items == 0:
                continue
            plugin_id = page.data[0].plugin_id

            group = groups.get(plugin_id, None)
            if group is None:
                groups[plugin_id] = [task_id]
            else:
                group.append(task_id)

        # write to csv files for each source
        for plugin_id, task_ids in groups.items():
            csv_file = work_dir / f"{plugin_dict[plugin_id]}.csv"
            await self._write_to_csv(
                Filters(filters={"task_id__in": task_ids}),
                plugin_dict,
                csv_file,
                delimiter,
            )

    def _zip_dir(self, src: Path, dest_zip: Path) -> None:
        src = src.resolve()
        with zipfile.ZipFile(dest_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(src.rglob("*")):
                rel = path.relative_to(src).as_posix()
                arcname = f"{src.name}/{rel}"

                zf.write(path, arcname)

    @staticmethod
    def build_task_set_key(
        task_ids: list[str],
        export_option: ExportOption,
    ) -> str:
        sorted_ids = sorted({str(t) for t in task_ids})
        payload = {
            "export_option": str(export_option),
            "task_ids": sorted_ids,
        }

        canonical = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    async def export_data(
        self, filters: Filters, export_option: ExportOption, delimiter=","
    ):
        # Does the archive exist already?
        # If so, return it
        task_ids = filters.filters["task_id__in"]
        task_set_hash = await run_in_threadpool(
            ExportService.build_task_set_key, task_ids, export_option
        )
        filename = await self._get_export_filename_by_hash(task_set_hash)
        if filename is not None:
            return filename

        plugins_page = await self._plugin_service.list_plugins()
        plugin_dict = {dto.id: dto.name for dto in plugins_page.data}

        # create the working directory
        work_dir = settings.TEMP_DIR / str(uuid4())
        os.mkdir(work_dir)

        if export_option == ExportOption.single_file:
            await self._export_to_single_file(filters, plugin_dict, work_dir, delimiter)

        elif export_option == ExportOption.by_sources:
            await self._export_by_sources(filters, plugin_dict, work_dir, delimiter)

        elif export_option == ExportOption.raw_data:
            await self._export_raw_data(filters, work_dir, plugin_dict)

        else:
            raise ValueError("Invalid export option")

        # create the result archive for export
        zip_file_path = settings.TEMP_DIR / f"{str(uuid4())}.zip"
        await run_in_threadpool(self._zip_dir, work_dir, zip_file_path)

        # remove working directory
        await run_in_threadpool(shutil.rmtree, work_dir)

        # create DB record for the archive
        await self._export_repository.save(
            ExportFile(
                file_name=str(zip_file_path.name),
                export_option=export_option,
                task_set_hash=task_set_hash,
            )
        )

        return zip_file_path

    async def _export_raw_data(
        self, filters: Filters, work_dir: Path, plugin_dict: dict[UUID, PluginDto]
    ):
        task_ids = filters.filters["task_id__in"]

        for task_id in task_ids:
            page = await self._data_service.list_photometric_data(
                count=1, filters=Filters(filters={"task_id__eq": task_id})
            )
            if page.total_items == 0:
                continue
            plugin_id = page.data[0].plugin_id
            source_name = plugin_dict[plugin_id]

            await run_in_threadpool(
                shutil.move,
                settings.TEMP_DIR / f"{task_id}.csv",
                work_dir / f"{source_name}_{task_id}.csv",
            )

    async def _get_export_filename_by_hash(self, task_set_hash: str) -> str | None:
        total, result = await self._export_repository.find(
            filters=Filters(filters={"task_set_hash__eq": task_set_hash})
        )
        if total == 0:
            return None
        return result[0].file_name
