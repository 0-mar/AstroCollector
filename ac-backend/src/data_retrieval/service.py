from typing import Annotated

from fastapi import Depends

from src.core.config.config import settings
from src.plugin.interface.schemas import PhotometricDataDto
from src.core.repository.repository import Repository, get_repository, Filters
from src.core.service.schemas import PaginationResponseDto
from src.data_retrieval.schemas import StellarObjectIdentifierDto
from src.tasks.model import StellarObjectIdentifier, PhotometricData

StellarObjectIdentifierRepositoryDep = Annotated[
    Repository[StellarObjectIdentifier],
    Depends(get_repository(StellarObjectIdentifier)),
]
PhotometricDataRepositoryDep = Annotated[
    Repository[PhotometricData], Depends(get_repository(PhotometricData))
]


class DataService:
    """
    Service to retrieve identifiers and photometric data from the database.
    """

    def __init__(
        self,
        soi_repository: StellarObjectIdentifierRepositoryDep,
        photometric_data_repository: PhotometricDataRepositoryDep,
    ):
        self._soi_repository = soi_repository
        self._photometric_data_repository = photometric_data_repository

    async def list_soi(
        self,
        offset: int = 0,
        count: int = settings.MAX_PAGINATION_BATCH_COUNT,
        filters: Filters | None = None,
    ) -> PaginationResponseDto[StellarObjectIdentifierDto]:
        total_count, soi_list = await self._soi_repository.find(
            offset=offset, count=count, filters=filters
        )
        data = list(map(StellarObjectIdentifierDto.model_validate, soi_list))
        return PaginationResponseDto[StellarObjectIdentifierDto](
            data=data, count=len(data), total_items=total_count
        )

    async def list_photometric_data(
        self,
        offset: int = 0,
        count: int = settings.MAX_PAGINATION_BATCH_COUNT,
        filters: Filters | None = None,
    ) -> PaginationResponseDto[PhotometricDataDto]:
        total_count, pd_list = await self._photometric_data_repository.find(
            offset=offset, count=count, filters=filters
        )

        data = list(map(PhotometricDataDto.model_validate, pd_list))
        return PaginationResponseDto[PhotometricDataDto](
            data=data, count=len(data), total_items=total_count
        )
