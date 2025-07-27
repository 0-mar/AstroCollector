from typing import Callable, Awaitable, Any

from celery import Celery
from sqlalchemy import insert

from src.core.config.config import settings
from src.core.database.database import async_sessionmanager
from src.core.integration.schemas import StellarObjectIdentificatorDto
from src.core.repository.repository import Repository
from src.core.repository.schemas import BaseDto
from src.plugin.model import Plugin
from src.plugin.service import PluginService
from src.tasks.model import StellarObjectIdentifier, PhotometricData, TaskBase
from src.tasks.schemas import ConeSearchRequestDto, FindObjectRequestDto
from src.tasks.service import StellarObjectService
from asgiref.sync import async_to_sync


# Configure Celery to use Redis as the message broker
celery_app = Celery(
    "worker",  # This is the name of your Celery application
    broker=f"redis://localhost:{settings.CACHE_PORT}/0",  # This is the Redis connection string
    backend=f"redis://localhost:{settings.CACHE_PORT}/0",
)


# async def _run_cone_search(job_id: str, search_query_dto: ConeSearchRequestDto):
#     async with async_sessionmanager.session() as session:
#         plugin_repo = Repository(Plugin, session)
#         plugin_service = PluginService(plugin_repo)
#         stellar_service = StellarObjectService(plugin_service)
#
#         objects = await stellar_service.catalogue_cone_search(search_query_dto)
#
#         print(f"[Job {job_id}] Found {len(objects)} stellar objects")
#
#         # convert values for bulk insert
#         values = [{"job_id": job_id, "identifier": dto.model_dump()} for dto in objects]
#         stmt = insert(StellarObjectIdentifier)
#         await session.execute(stmt, values)
#
#
# @celery.task(bind=True)
# def cone_search(self, search_query_dto: ConeSearchRequestDto):
#     return asyncio.run(_run_cone_search(self.request.id, search_query_dto))
#
#
# async def _run_find_stellar_object(job_id: str, find_object_query_dto: FindObjectRequestDto):
#     async with async_sessionmanager.session() as session:
#         plugin_repo = Repository(Plugin, session)
#         plugin_service = PluginService(plugin_repo)
#         stellar_service = StellarObjectService(plugin_service)
#
#         objects = await stellar_service.find_stellar_object(find_object_query_dto)
#
#         print(f"[Job {job_id}] Found {len(objects)} stellar objects")
#
#         # convert values for bulk insert
#         values = [{"job_id": job_id, "identifier": dto.model_dump()} for dto in objects]
#         stmt = insert(StellarObjectIdentifier)
#         await session.execute(stmt, values)
#
#
# @celery.task(bind=True)
# def find_object(self, find_object_query_dto: FindObjectRequestDto):
#     return asyncio.run(_run_find_stellar_object(self.request.id, find_object_query_dto))
#
#
# async def _run_get_photometric_data(job_id: str, identifier_model: StellarObjectIdentificatorDto):
#     async with async_sessionmanager.session() as session:
#         plugin_repo = Repository(Plugin, session)
#         plugin_service = PluginService(plugin_repo)
#         stellar_service = StellarObjectService(plugin_service)
#
#         data = await stellar_service.get_photometric_data(identifier_model)
#
#         print(f"[Job {job_id}] Found {len(data)} results")
#
#         # convert values for bulk insert
#         values = [{"job_id": job_id, **dto.model_dump()} for dto in data]
#         stmt = insert(PhotometricData)
#         await session.execute(stmt, values)
#
#
# @celery.task(bind=True)
# def get_photometric_data(self, identifier_model: StellarObjectIdentificatorDto):
#     return asyncio.run(_run_get_photometric_data(self.request.id, identifier_model))


async def _run_task(
    job_id: str,
    service_method: Callable[[StellarObjectService, BaseDto], Awaitable[list[BaseDto]]],
    input_dto_dict: dict[str, Any],
    table: type[TaskBase],
    mapping: Callable[[str, BaseDto], dict[str, Any]],
    dto_model: type[BaseDto],
):
    input_dto = dto_model.model_validate(input_dto_dict)
    async with async_sessionmanager.session() as session:
        plugin_repo = Repository(Plugin, session)
        plugin_service = PluginService(plugin_repo)
        stellar_service = StellarObjectService(plugin_service)

        data = await service_method(stellar_service, input_dto)

        print(f"[Job {job_id}] Found {len(data)} results")

        # convert values for bulk insert
        values = [mapping(job_id, dto) for dto in data]
        stmt = insert(table)
        await session.execute(stmt, values)
        await session.commit()


# https://stackoverflow.com/questions/39815771/how-to-combine-celery-with-asyncio
def _task_wrapper(
    service_method: Callable[[StellarObjectService, BaseDto], Awaitable[list[BaseDto]]],
    table: type[TaskBase],
    mapping: Callable[[str, BaseDto], dict[str, Any]],
    dto_model: type[BaseDto],
    name: str,
):
    @celery_app.task(bind=True, name=name)
    def run_task(self, input_dto: dict[str, Any]):
        async_to_sync(_run_task)(
            self.request.id, service_method, input_dto, table, mapping, dto_model
        )
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        # try:
        #     result = loop.run_until_complete(
        #         _run_task(
        #             self.request.id,
        #             service_method,
        #             input_dto,
        #             table,
        #             mapping,
        #             dto_model
        #         )
        #     )
        #     print(f"[{name}] Task completed successfully.")
        #     return result
        # except Exception as e:
        #     print(f"[{name}] ❌ Exception during task execution: {repr(e)}")
        #     raise
        # finally:
        #     loop.close()
        #     print(f"[{name}] Event loop closed.")

        # loop = asyncio.get_event_loop()
        # return loop.run_until_complete(_run_task(self.request.id, service_method, input_dto, table, mapping, dto_model))

        # return asyncio.run(_run_task(self.request.id, service_method, input_dto, table, mapping, dto_model))

    return run_task


cone_search = _task_wrapper(
    lambda service, dto: service.catalogue_cone_search(dto),
    StellarObjectIdentifier,
    lambda task_id, dto: {"task_id": task_id, "identifier": dto.model_dump()},
    ConeSearchRequestDto,
    "cone-search",
)


find_object = _task_wrapper(
    lambda service, dto: service.find_stellar_object(dto),
    StellarObjectIdentifier,
    lambda task_id, dto: {"task_id": task_id, "identifier": dto.model_dump()},
    FindObjectRequestDto,
    "find-object",
)


get_photometric_data = _task_wrapper(
    lambda service, dto: service.get_photometric_data(dto),
    PhotometricData,
    lambda task_id, dto: {"task_id": task_id, **dto.model_dump()},
    StellarObjectIdentificatorDto,
    "get_photometric_data",
)
