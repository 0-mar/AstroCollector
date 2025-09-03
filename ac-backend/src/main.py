import logging
import logging.config
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from aiocache import Cache
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config.config import settings
from src.core.database.database import async_sessionmanager
from src.core.http_client import HttpClient
from src.core.repository.repository import Repository
from src.data_retrieval import router as data_router
from src.plugin import router as plugin_router
from src.plugin.model import Plugin
from src.plugin.service import PluginService
from src.tasks import router as task_router
from src.tasks.model import Task
from src.so_name_resolving import router as name_resolving_router
from src.phase_curve import router as phase_diagram_router

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@scheduler.scheduled_job("interval", hours=settings.TASK_DATA_DELETE_INTERVAL)
async def clear_task_data():
    logger.info("Clearing old task data")
    async with async_sessionmanager.session() as session:
        task_repository = Repository(Task, session)

        offset = 0
        total = 1

        while True:
            if offset >= total:
                break

            total, results = await task_repository.find(offset=offset, count=1000)
            offset += len(results)

            for task in results:
                if isinstance(task, Task):
                    if task.created < (
                        datetime.now()
                        - timedelta(hours=settings.TASK_DATA_DELETE_INTERVAL)
                    ):
                        await task_repository.delete(task.id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    HttpClient()
    logging.config.dictConfig(settings.LOGGING_CONFIG)

    # load plugins on startup
    async with async_sessionmanager.session() as session:
        plugin_repository = Repository(Plugin, session)
        plugin_service = PluginService(plugin_repository)
        await plugin_service.create_default_plugins()

    scheduler.start()

    yield

    scheduler.shutdown()
    await HttpClient().get_session().close()


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# cache: https://stackoverflow.com/questions/65686318/sharing-python-objects-across-multiple-workers
plugin_cache = Cache(
    Cache.REDIS, endpoint="localhost", port=settings.CACHE_PORT, namespace="main"
)

app.include_router(plugin_router.router)
app.include_router(task_router.router)
app.include_router(data_router.router)
app.include_router(name_resolving_router.router)
app.include_router(phase_diagram_router.router)
