from typing import List, Any

from fastapi import FastAPI
from pydantic import BaseModel
import requests

from src.core.integration.schemas import PhotometricDataModel
from src.dasch.dasch_identificator_model import DaschIdentificatorModel
from src.dasch.dasch_plugin import DaschPlugin
from src.plugin import plugin_router

app = FastAPI()

app.include_router(plugin_router.router)


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
async def dasch(query: Query) -> List[PhotometricDataModel]:
    d = DaschPlugin()
    m = DaschIdentificatorModel(
        ra_deg=query.ra_deg,
        dec_deg=query.dec_deg,
        gsc_bin_index=137593564,
        ref_number=110303213195875,
    )
    return d.get_photometric_data(m)
