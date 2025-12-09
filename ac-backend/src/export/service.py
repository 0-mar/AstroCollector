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
    """
    Handles data export functionality - exporting to a single file, by sources, or as raw data.
    Provides methods for managing the export process.

    :ivar _export_repository: Repository dependency for managing export records.
    :type _export_repository: ExportRepositoryDep
    :ivar _plugin_service: Service dependency for accessing plugin-related data.
    :type _plugin_service: PluginServiceDep
    :ivar _data_service: Service dependency for accessing photometric data.
    :type _data_service: DataServiceDep
    """

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
    ) -> None:
        """
        Asynchronously writes photometric data to a CSV file, formatted with a specific delimiter
        and header. The data is filtered based on the provided filters.

        :param filters: The filtering criteria used to retrieve photometric data.
        :type filters: Filters
        :param plugin_dict: A dictionary mapping plugin UUIDs to corresponding PluginDto objects.
        :type plugin_dict: dict[UUID, PluginDto]
        :param csv_file: Path to the CSV file where data will be written.
        :type csv_file: Path
        :param delimiter: The delimiter used to separate values in the CSV file.
        :type delimiter: str
        :return: None
        :rtype: None
        """
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
    ) -> None:
        """
        Asynchronously exports all photometric data (from all tasks) to a single CSV file. The data is written to a file named
        "export.csv" in the specified working directory.

        :param filters: The filtering criteria used to retrieve photometric data.
        :type filters: Filters
        :param plugin_dict: A dictionary mapping plugin UUIDs to corresponding PluginDto objects.
        :type plugin_dict: dict[UUID, PluginDto]
        :param work_dir: The directory where the resulting CSV file will be created.
        :type work_dir: Path
        :param delimiter: The string character used to separate values in the resulting
            CSV file.
        :type delimiter: str
        :return: None
        :rtype: None
        """
        csv_file = work_dir / "export.csv"
        await self._write_to_csv(filters, plugin_dict, csv_file, delimiter)

    async def _export_by_sources(
        self, filters, plugin_dict, work_dir, delimiter
    ) -> None:
        """
        Asynchronously exports task data grouped by source to separate CSV files. The tasks
        are split based on their respective plugin IDs, retrieved via the associated plugin
        data.

        :param filters: Task ID filters
        :type filters: Filters
        :param plugin_dict: A dictionary mapping plugin UUIDs to corresponding PluginDto objects.
        :type plugin_dict: dict[UUID, PluginDto]
        :param work_dir: The directory where the output CSV files will be saved.
        :type work_dir: pathlib.Path
        :param delimiter: The delimiter to be used in the output CSV files.
        :type delimiter: str
        :return: None
        :rtype: None
        """
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
        """
        Compresses all files from a source directory into a
        specified zip file using ZIP_DEFLATED compression. Recursively traverses the
        entire directory structure and maintains relative paths for all files.

        :param src: The source directory to be zipped.
        :type src: Path
        :param dest_zip: The path where the resulting zip file will be created.
        :type dest_zip: Path
        :return: None
        :rtype: None
        """
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
        """
        Builds a deterministic key for a set of tasks and an export option.

        This method computes a key by creating a payload consisting of the sorted list
        of task IDs and the string representation of the export option. It then
        generates a SHA-256 hash of the JSON-encoded payload to ensure that the key is
        unique and consistent for the same inputs.

        :param task_ids: List of task IDs for which the key is to be generated.
        :type task_ids: list[str]
        :param export_option: The export option to be included in the key.
        :type export_option: ExportOption
        :return: A SHA-256 hash string representing the unique key for the task set and
                 export option.
        :rtype: str
        """
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
        """
        Exports data based on the provided filters and export option. The export process
        includes creating a working directory, processing export data into the required
        format, zipping the result into an archive, and recording the archive details in
        the database. If an export archive with the specified task ID and export option
        already exists, it will return the existing archive instead of creating a new one.

        :param filters: Filters to select data for the export
        :type filters: Filters
        :param export_option: Type of export operation to perform
        :type export_option: ExportOption
        :param delimiter: Delimiter to use for CSV files in the export. For raw data export, this does not matter.
        :type delimiter: str
        :return: Path to the exported archive file
        :rtype: str
        """
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
        """
        Exports raw photometric data from specified tasks in the filters object,
        renaming them according to their source and task identifier.

        :param filters: Filters object specifying filter criteria for tasks to export
        :param work_dir: Directory path where the exported files will be moved to and stored
        :param plugin_dict: A dictionary mapping plugin UUIDs to corresponding PluginDto objects.
        :return: None
        """
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
        """
        Gets the export file name associated with a given task set hash. If no matching task set is found
        in the repository, the function returns None.

        :param task_set_hash: The hash string associated with a task set that
            uniquely identifies it within the export repository.
        :type task_set_hash: str

        :return: The file name for the given task set hash if found, otherwise None.
        :rtype: str | None
        """
        total, result = await self._export_repository.find(
            filters=Filters(filters={"task_set_hash__eq": task_set_hash})
        )
        if total == 0:
            return None
        return result[0].file_name
