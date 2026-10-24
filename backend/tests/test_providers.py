import httpx
import pytest

from app.core.errors import ApiError
from app.services.providers import OpenMeteoClient


def client(handler, retries: int = 0) -> OpenMeteoClient:
    return OpenMeteoClient(
        "https://weather.example/v1",
        "https://air.example/v1",
        timeout_seconds=0.1,
        retries=retries,
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_provider_retries_upstream_error_then_returns_json():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503 if attempts == 1 else 200, json={"ok": True})

    assert await client(handler, retries=1)._request("https://weather.example", {}) == {
        "ok": True
    }
    assert attempts == 2


@pytest.mark.asyncio
async def test_provider_rate_limit_is_predictable_after_retries():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"reason": "slow down"})

    with pytest.raises(ApiError, match="rate limiting") as error:
        await client(handler, retries=1)._request("https://weather.example", {})
    assert error.value.status_code == 503
    assert error.value.code == "provider_rate_limited"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "handler",
    [
        lambda request: httpx.Response(200, content=b"not-json"),
        lambda request: httpx.Response(200, json=["not", "an", "object"]),
    ],
)
async def test_provider_rejects_malformed_payloads(handler):
    with pytest.raises(ApiError) as error:
        await client(handler)._request("https://weather.example", {})
    assert error.value.code == "provider_unavailable"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception", [httpx.ConnectError("offline"), httpx.ReadTimeout("timed out")]
)
async def test_provider_connection_failures_are_predictable(exception):
    def handler(request: httpx.Request) -> httpx.Response:
        raise exception

    with pytest.raises(ApiError) as error:
        await client(handler)._request("https://weather.example", {})
    assert error.value.status_code == 503
    assert error.value.code == "provider_unavailable"
