import logging
import logging.config
import os
from contextlib import asynccontextmanager
from pathlib import Path

from astropy.coordinates.name_resolve import NameResolveError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient, Client
from starlette import status
from starlette.responses import JSONResponse

from src.core.config.config import settings
from src.core.database.db_init import init_db
from src.core.exception.exceptions import ACException
from src.core.security import router as security_router
from src.data_retrieval import router as data_router
from src.export import router as export_router
from src.phase_curve import router as phase_diagram_router
from src.plugin import router as plugin_router
from src.so_name_resolving import router as name_resolving_router
from src.tasks import router as task_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # create log directory if not present
    if not Path.exists(settings.LOGGING_DIR):
        os.mkdir(settings.LOGGING_DIR)

    # create temp directory if not present
    if not Path.exists(settings.TEMP_DIR):
        os.mkdir(settings.TEMP_DIR)

    # create resources directory if not present
    if not Path.exists(settings.RESOURCES_DIR):
        os.mkdir(settings.RESOURCES_DIR)

    logging.config.dictConfig(settings.LOGGING_CONFIG)
    for uvicorn_logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    ):
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.setLevel(logging.INFO)
        uvicorn_logger.propagate = True  # send to root

    await init_db()

    sync_http_client = Client()
    async with AsyncClient() as http_client:
        yield {"async_http_client": http_client, "sync_http_client": Client()}
        # The AsyncClient closes on shutdown

    sync_http_client.close()


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

    if isinstance(exc, NameResolveError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error_message": str(exc),
                "code": "SO_NAME_RESOLVE_ERROR",
                "status": status.HTTP_404_NOT_FOUND,
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

app.include_router(plugin_router.router)
app.include_router(task_router.router)
app.include_router(data_router.router)
app.include_router(name_resolving_router.router)
app.include_router(phase_diagram_router.router)
app.include_router(export_router.router)
app.include_router(security_router.router)
