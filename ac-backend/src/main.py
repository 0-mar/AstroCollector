import logging
import logging.config
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from aiocache import Cache
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.responses import JSONResponse

from src.core.config.config import settings
from src.core.database.database import async_sessionmanager
from src.core.database.db_init import init_db
from src.core.exception.exceptions import ACException
from src.core.http_client import HttpClient
from src.core.repository.repository import Repository
from src.data_retrieval import router as data_router
from src.plugin import router as plugin_router
from src.tasks import router as task_router
from src.tasks.model import Task
from src.so_name_resolving import router as name_resolving_router
from src.phase_curve import router as phase_diagram_router
from src.export import router as export_router
from src.core.security import router as security_router

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
                    if task.created_at < (
                        datetime.now()
                        - timedelta(hours=settings.TASK_DATA_DELETE_INTERVAL)
                    ):
                        await task_repository.delete(task.id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    HttpClient()
    logging.config.dictConfig(settings.LOGGING_CONFIG)

    await init_db()
    scheduler.start()

    yield

    scheduler.shutdown()
    await HttpClient().get_session().close()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_message": exc.detail,
            "code": "NO_CODE",
            "status": exc.status_code,
        },
        headers=headers,
    )


@app.exception_handler(Exception)
async def validation_exception_handler(request, exc: Exception):
    logger.exception("An exception occured: %s %s", request.method, request.url)

    if isinstance(exc, ACException):
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error_message": exc.message,
                "code": exc.code,
                "status": exc.http_status,
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_message": str(exc) if settings.DEBUG else "Internal server error",
            "code": "NO_CODE",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


# frontend ports
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
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
app.include_router(export_router.router)
app.include_router(security_router.router)
