from typing import Annotated

from fastapi import Depends

from src.tasks.schemas import ConeSearchRequestDto
from src.tasks.service import StellarObjectService

StellarObjectServiceServiceDep = Annotated[
    StellarObjectService, Depends(StellarObjectService)
]


async def cone_search_task(
    search_query_dto: ConeSearchRequestDto, so_service: StellarObjectServiceServiceDep
):
    # data = await so_service.catalogue_cone_search(search_query_dto)
    #
    # print(f"[Job {job_id}] Found {len(data)} results")
    #
    # # convert values for bulk insert
    # values = [mapping(job_id, dto) for dto in data]
    # stmt = insert(table)
    pass
