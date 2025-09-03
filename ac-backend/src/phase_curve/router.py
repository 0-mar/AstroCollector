from astropy.coordinates import SkyCoord
from fastapi import APIRouter

from src.core.exception.exceptions import APIException
from src.core.http_client import HttpClient
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
            "Epoch" not in record
            or "Period" not in record
            or "RA2000" not in record
            or "Declination2000" not in record
        ):
            continue
        return PhaseCurveDataDto(
            ra_deg=float(record["RA2000"]),
            dec_deg=float(record["Declination2000"]),
            epoch=float(record["Epoch"]),
            period=float(record["Period"]),
            vsx_object_name=record["Name"] if "Name" in record else "",
        )

    return PhaseCurveDataDto(
        ra_deg=None, dec_deg=None, epoch=None, period=None, vsx_object_name=None
    )


@router.get("")
async def phase_curve_data(
    name: str | None = None, ra_deg: float | None = None, dec_deg: float | None = None
) -> PhaseCurveDataDto:
    """
    Get the period and epoch of a star given by its name, or coordinates.
    If both are provided, the name is used as first and if the search fails, the coordinates are used.
    VSX catalog (https://vsx.aavso.org/) is used to get the data.
    :param name:
    :param ra_deg:
    :param dec_deg:
    :return:
    """

    if name is None and (ra_deg is None or dec_deg is None):
        raise APIException("Provide name or ra_deg and dec_deg in query params.")

    http_client = HttpClient().get_session()

    if name is not None:
        async with http_client.get(
            f"https://vsx.aavso.org/index.php?view=api.object&ident={name}&format=json"
        ) as query_resp:
            query_data = await query_resp.json()

        if query_data["VSXObject"] != []:
            record = query_data["VSXObject"]
            if (
                "Epoch" in record
                and "Period" in record
                and "RA2000" in record
                and "Declination2000" in record
            ):
                return PhaseCurveDataDto(
                    ra_deg=float(record["RA2000"]),
                    dec_deg=float(record["Declination2000"]),
                    epoch=float(record["Epoch"]),
                    period=float(record["Period"]),
                    vsx_object_name=record["Name"] if "Name" in record else "",
                )

    if ra_deg is not None and dec_deg is not None:
        async with http_client.get(
            f"https://vsx.aavso.org/index.php?view=api.list&ra={ra_deg}&dec={dec_deg}&radius={30 / 3600}&format=json"
        ) as query_resp:
            query_data = await query_resp.json()

        return get_phase_curve_data(query_data, SkyCoord(ra_deg, dec_deg, unit="deg"))

    return PhaseCurveDataDto(
        ra_deg=None, dec_deg=None, epoch=None, period=None, vsx_object_name=None
    )
