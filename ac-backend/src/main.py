from typing import List, Any

from fastapi import FastAPI
from pydantic import BaseModel
import requests
from aiocache import Cache

from src.core.http_client import HttpClient
from src.core.integration.schemas import PhotometricDataDto
from src.dasch.dasch_identificator_model import DaschStellarObjectIdentificatorDto
from src.dasch.dasch_plugin import DaschPlugin
from src.plugin import plugin_router
from src.data_retriever import router as data_router
from src.core.config.config import settings


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


@app.get("/")
async def root() -> Any:
    url = "https://api.starglass.cfa.harvard.edu/public/dasch/dr7/lightcurve"
    headers = {"accept": "application/json", "Content-Type": "application/json"}
    data = {
        "gsc_bin_index": 137593564,
        "ref_number": 110303213195875,
        "refcat": "apass",
    }

    # test
    response = requests.post(url, headers=headers, json=data)
    return response.json()


@app.get("/hello/{name}")
async def say_hello(name: str) -> Any:
    return {"message": f"Hello {name}"}


class Query(BaseModel):
    ra_deg: float
    dec_deg: float
    radius_arcsec: float


@app.post("/dasch")
async def dasch(query: Query) -> List[PhotometricDataDto]:
    d = DaschPlugin()
    m = DaschStellarObjectIdentificatorDto(
        ra_deg=query.ra_deg,
        dec_deg=query.dec_deg,
        gsc_bin_index=137593564,
        ref_number=110303213195875,
    )
    return d.get_photometric_data(m)
