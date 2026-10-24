import httpx
import pytest

from app.services.providers import OpenMeteoClient


@pytest.mark.asyncio
async def test_historical_request_is_pinned_to_era5_reanalysis():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(request.url.params)
        return httpx.Response(200, json={"daily": {"time": ["2024-01-01"]}})

    client = OpenMeteoClient(
        "https://weather.example/v1",
        "https://air.example/v1",
        timeout_seconds=1,
        retries=0,
        transport=httpx.MockTransport(handler),
    )

    await client.archive(28.6, 77.2, "Asia/Kolkata", "2024-01-01", "2024-01-01")

    assert captured["models"] == "era5"
