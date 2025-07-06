from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)
from src.data_retriever.schemas import SearchQueryRequestDto, FindObjectQueryRequestDto
from src.data_retriever.service import StellarObjectService

StellarObjectServiceDep = Annotated[StellarObjectService, Depends(StellarObjectService)]

router = APIRouter(
    prefix="/api/photometric-data",
    tags=["photometric-data"],
    responses={404: {"description": "Not found"}},
)


@router.post("/search-catalogues", response_model=dict[UUID, list[Any]])
async def search_catalogues(
    service: StellarObjectServiceDep, search_query_dto: SearchQueryRequestDto
) -> dict[UUID, list[StellarObjectIdentificatorDto]]:
    return await service.search_catalogues_by_coords(search_query_dto)


@router.post("/find-object", response_model=dict[UUID, Any])
async def find_object(
    service: StellarObjectServiceDep, find_object_query_dto: FindObjectQueryRequestDto
) -> dict[UUID, StellarObjectIdentificatorDto]:
    return await service.find_stellar_object_in_catalogues(find_object_query_dto)


@router.post("/retrieve/{plugin_id}", response_model=list[PhotometricDataDto])
async def retrieve_data(
    service: StellarObjectServiceDep,
    identificator_model: StellarObjectIdentificatorDto,
) -> list[PhotometricDataDto]:
    return await service.get_photometric_data(identificator_model)


@router.post("/retrieve", response_model=list[PhotometricDataDto])
async def retrieve_data_multiple_sources(
    service: StellarObjectServiceDep,
    identificator_models: list[StellarObjectIdentificatorDto],
) -> dict[UUID, list[PhotometricDataDto]]:
    return await service.get_photometric_data_multiple_sources(identificator_models)
