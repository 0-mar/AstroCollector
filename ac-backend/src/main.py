from typing import List

from fastapi import FastAPI
from pydantic import BaseModel
import requests

from src.core.integration.schemas import PhotometricDataModel
from src.dasch.dasch_plugin import DaschPlugin
from src.plugin import plugin_router

app = FastAPI()

app.include_router(plugin_router.router)

@app.get("/")
async def root():
    url = 'https://api.starglass.cfa.harvard.edu/public/dasch/dr7/lightcurve'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "gsc_bin_index": 137593564,
        "ref_number": 110303213195875,
        "refcat": "apass"
    }

    response = requests.post(url, json=data)
    return response.json()


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

class Query(BaseModel):
    ra_deg: float
    dec_deg: float
    radius_arcsec: float

@app.post("/dasch")
async def dasch(query: Query) -> List[PhotometricDataModel]:
    d = DaschPlugin()
    return d.get_data(query.ra_deg, query.dec_deg, query.radius_arcsec)
