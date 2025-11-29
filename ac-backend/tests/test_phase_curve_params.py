import httpx

LIVE_VSX_URL = "https://vsx.aavso.org/index.php"


def test_live_vsx_api_format():
    params = {
        "view": "api.object",
        "ident": "V Lep",
        "format": "json",
    }

    resp = httpx.get(LIVE_VSX_URL, params=params, timeout=10.0)
    resp.raise_for_status()

    data = resp.json()
    print(data)  # helpful when running locally

    assert "VSXObject" in data
    record = data["VSXObject"]
    assert "RA2000" in record
    assert "Declination2000" in record
    assert "Period" in record
    assert "Epoch" in record
