from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from src.core.integration.schemas import (
    StellarObjectIdentificatorDto,
    PhotometricDataDto,
)
from src.data_retriever.schemas import ConeSearchRequestDto, FindObjectRequestDto
from src.data_retriever.service import StellarObjectService

StellarObjectServiceDep = Annotated[StellarObjectService, Depends(StellarObjectService)]

router = APIRouter(
    prefix="/api/photometric-data",
    tags=["photometric-data"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{plugin_id}/cone-search", response_model=list[Any])
async def cone_search(
    service: StellarObjectServiceDep,
    search_query_dto: ConeSearchRequestDto,
    plugin_id: UUID,
) -> list[StellarObjectIdentificatorDto]:
    search_query_dto.plugin_id = plugin_id
    return await service.catalogue_cone_search(search_query_dto)


@router.post("/{plugin_id}/find-object", response_model=list[Any])
async def find_object(
    service: StellarObjectServiceDep,
    find_object_query_dto: FindObjectRequestDto,
    plugin_id: UUID,
) -> list[StellarObjectIdentificatorDto]:
    find_object_query_dto.plugin_id = plugin_id
    return await service.find_stellar_object(find_object_query_dto)


# @router.post("/{plugin_id}/retrieve", response_model=list[PhotometricDataDto])
@router.post("/{plugin_id}/retrieve")
async def retrieve_data(
    service: StellarObjectServiceDep,
    plugin_id: UUID,
    identificator_model: StellarObjectIdentificatorDto,
):  # -> list[PhotometricDataDto]:
    identificator_model.plugin_id = plugin_id

    json_compatible_item_data = jsonable_encoder(
        await service.get_photometric_data(identificator_model)
    )
    return JSONResponse(content=json_compatible_item_data)
    # return await service.get_photometric_data(identificator_model)


@router.post("/retrieve", response_model=dict[UUID, list[PhotometricDataDto]])
async def retrieve_data_multiple_sources(
    service: StellarObjectServiceDep,
    identificator_models: list[StellarObjectIdentificatorDto],
) -> dict[UUID, list[PhotometricDataDto]]:
    return await service.get_photometric_data_multiple_sources(identificator_models)
