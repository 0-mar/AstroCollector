from aiocache import Cache
from fastapi import FastAPI

from src.core.config.config import settings
from src.core.http_client import HttpClient
from src.data_retriever import router as data_router
from src.plugin import router as plugin_router


async def on_start_up() -> None:
    HttpClient()


async def on_shutdown() -> None:
    await HttpClient().get_session().close()


app = FastAPI(on_startup=[on_start_up], on_shutdown=[on_shutdown])
# cache: https://stackoverflow.com/questions/65686318/sharing-python-objects-across-multiple-workers
plugin_cache = Cache(
    Cache.REDIS, endpoint="localhost", port=settings.CACHE_PORT, namespace="main"
)

app.include_router(plugin_router.router)
app.include_router(data_router.router)
