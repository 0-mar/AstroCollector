from src.core.repository.schemas import BaseDto


class PaginationResponseDto[DataT](BaseDto):
    data: list[DataT]
    count: int
    total_items: int
