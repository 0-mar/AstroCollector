from astropy.coordinates import SkyCoord
from fastapi import APIRouter, Depends
from httpx import AsyncClient

from src.core.exception.exceptions import APIException

from src.deps import get_async_http_client
from src.phase_curve.schemas import PhaseCurveDataDto


router = APIRouter(
    prefix="/api/phase-curve",
    tags=["so-name-resolving"],
    responses={404: {"description": "Not found"}},
)


def get_phase_curve_data(query_data, search_coords: SkyCoord):
    """
    Return the period and epoch of a star closest to the search coordinates.
    :param query_data:
    :param search_coords:
    :return:
    """
    if query_data["VSXObjects"] == []:
        return PhaseCurveDataDto(
            ra_deg=None, dec_deg=None, epoch=None, period=None, vsx_object_name=None
        )

    def sort_by_dist(record):
        return search_coords.separation(
            SkyCoord(record["RA2000"], record["Declination2000"], unit="deg")
        ).arcsec

    for record in sorted(query_data["VSXObjects"]["VSXObject"], key=sort_by_dist):
        if (
            "Period" not in record
            or "RA2000" not in record
            or "Declination2000" not in record
        ):
            continue
        return PhaseCurveDataDto(
            ra_deg=float(record["RA2000"]),
            dec_deg=float(record["Declination2000"]),
            epoch=float(record["Epoch"]) if "Epoch" in record else None,
            period=float(record["Period"]),
            vsx_object_name=record["Name"] if "Name" in record else None,
        )

    return PhaseCurveDataDto(
        ra_deg=None, dec_deg=None, epoch=None, period=None, vsx_object_name=None
    )


@router.get("")
async def phase_curve_data(
    http_client: AsyncClient = Depends(get_async_http_client),
    name: str | None = None,
    ra_deg: float | None = None,
    dec_deg: float | None = None,
) -> PhaseCurveDataDto:
    """
    Get the period and epoch of a star given by its name, or coordinates.
    If both are provided, the name is used as first and if the search fails, the coordinates are used.
    VSX catalog (https://vsx.aavso.org/) is used to get the data.
    :param http_client:
    :param name:
    :param ra_deg:
    :param dec_deg:
    :return:
    """

    if name is None and (ra_deg is None or dec_deg is None):
        raise APIException("Provide name or ra_deg and dec_deg in query params.")

    if name is not None:
        params = {"format": "json", "view": "api.object", "ident": name}
        query_resp = await http_client.get(
            "https://vsx.aavso.org/index.php", params=params
        )
        query_data = query_resp.json()

        if query_data["VSXObject"] != []:
            record = query_data["VSXObject"]
            if (
                "Period" in record
                and "RA2000" in record
                and "Declination2000" in record
            ):
                return PhaseCurveDataDto(
                    ra_deg=float(record["RA2000"]),
                    dec_deg=float(record["Declination2000"]),
                    epoch=float(record["Epoch"]) if "Epoch" in record else None,
                    period=float(record["Period"]),
                    vsx_object_name=record["Name"] if "Name" in record else None,
                )

    if ra_deg is not None and dec_deg is not None:
        params = {
            "format": "json",
            "view": "api.list",
            "ra": ra_deg,
            "dec": dec_deg,
            "radius": 30 / 3600,
        }
        query_resp = await http_client.get(
            "https://vsx.aavso.org/index.php", params=params
        )
        query_data = query_resp.json()

        return get_phase_curve_data(query_data, SkyCoord(ra_deg, dec_deg, unit="deg"))

    return PhaseCurveDataDto(
        ra_deg=None, dec_deg=None, epoch=None, period=None, vsx_object_name=None
    )
