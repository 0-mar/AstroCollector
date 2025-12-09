from fastapi import APIRouter, Depends
from httpx import Client

from src.deps import get_sync_http_client
from src.so_name_resolving.schemas import ResolvedCoordsDto, StellarObjectNameDto
from src.tasks.tasks import (
    resolve_name_to_coordinates,
)

router = APIRouter(
    prefix="/api/so-name-resolve",
    tags=["so-name-resolving"],
    responses={404: {"description": "Not found"}},
)


@router.post("")
def resolve_name(
    requested_name: StellarObjectNameDto,
    http_client: Client = Depends(get_sync_http_client),
) -> ResolvedCoordsDto:
    """Resolve a stellar object name to coordinates."""
    coords = resolve_name_to_coordinates(requested_name.name, http_client)
    return ResolvedCoordsDto(ra_deg=coords.ra.deg, dec_deg=coords.dec.deg)
