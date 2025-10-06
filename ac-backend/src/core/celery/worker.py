from celery import Celery

from src.core.config.config import settings

# Initialize Celery with Redis as broker and result backend
celery_app = Celery(
    "ac_worker",
    broker=f"redis://redis:{settings.CACHE_PORT}/0",
    backend=f"redis://redis:{settings.CACHE_PORT}/0",
)
# Celery configuration for reliability and performance
celery_app.conf.update(
    result_expires=settings.TASK_DATA_DELETE_INTERVAL
    * 3600,  # Task results expire in 1 hour (cleanup)
    task_track_started=True,  # Enable tracking the STARTED state of tasks
    task_acks_late=True,  # Acknowledge tasks after execution, not before
    # task_reject_on_worker_lost=True,   # Reschedule task if worker crashes:contentReference[oaicite:19]{index=19}
    worker_prefetch_multiplier=1,  # Each worker grabs only 1 task at a time:contentReference[oaicite:20]{index=20}
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
# async def _run_find_stellar_object(
#     job_id: str, find_object_query_dto: FindObjectRequestDto
# ):
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
# async def _run_get_photometric_data(
#     job_id: str, identifier_model: StellarObjectIdentificatorDto
# ):
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
