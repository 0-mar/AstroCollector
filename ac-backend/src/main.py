from aiocache import Cache
from fastapi import FastAPI

from src.core.config.config import settings
from src.core.http_client import HttpClient
from src.tasks import router as task_router
from src.plugin import router as plugin_router
from src.data_retrieval import router as data_router
from fastapi.middleware.cors import CORSMiddleware


async def on_start_up() -> None:
    HttpClient()


async def on_shutdown() -> None:
    await HttpClient().get_session().close()


app = FastAPI(on_startup=[on_start_up], on_shutdown=[on_shutdown])

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
