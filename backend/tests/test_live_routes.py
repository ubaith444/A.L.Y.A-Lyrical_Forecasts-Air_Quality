from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import get_cache, get_provider
from app.main import app


class WeatherProvider:
    async def weather(self, **kwargs):
        return {
            "current": {"time": "2025-01-01T00:00", "temperature_2m": 25.0},
            "current_units": {"temperature_2m": "°C"},
            "hourly": {"time": ["2025-01-01T00:00"], "temperature_2m": [25.0]},
            "hourly_units": {"temperature_2m": "°C"},
            "daily": {"time": ["2025-01-01"], "temperature_2m_max": [26.0]},
            "daily_units": {"temperature_2m_max": "°C"},
        }


class MalformedWeatherProvider:
    async def weather(self, **kwargs):
        return {
            "current": {"time": "2025-01-01T00:00"},
            "hourly": {"time": ["2025-01-01T00:00"], "temperature_2m": [25.0, 26.0]},
            "daily": {"time": ["2025-01-01"], "temperature_2m_max": [26.0]},
        }


class AirQualityProvider:
    async def air_quality(self, **kwargs):
        return {
            "current": {"time": "2025-01-01T00:00", "us_aqi": 42, "pm2_5": None},
            "current_units": {"us_aqi": "", "pm2_5": "μg/m³"},
        }


class DirectCache:
    async def get_or_fetch(self, namespace, params, fetch):
        return await fetch(), False, datetime(2025, 1, 1, tzinfo=UTC)


def request_with(provider):
    app.dependency_overrides[get_provider] = lambda: provider
    app.dependency_overrides[get_cache] = lambda: DirectCache()
    try:
        return TestClient(app).get(
            "/api/v1/weather", params={"location_id": "new-delhi"}
        )
    finally:
        app.dependency_overrides.clear()


def test_weather_route_normalizes_valid_provider_payload():
    response = request_with(WeatherProvider())

    assert response.status_code == 200
    body = response.json()
    assert body["current"]["values"]["temperature_2m"] == 25.0
    assert body["provenance"]["retrieved_at"] == "2025-01-01T00:00:00+00:00"
    assert body["provenance"]["freshness"] == "fresh"


def test_weather_route_rejects_misaligned_provider_series():
    response = request_with(MalformedWeatherProvider())

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "provider_invalid_response"


def test_air_quality_keeps_missing_pollutant_unavailable():
    app.dependency_overrides[get_provider] = lambda: AirQualityProvider()
    app.dependency_overrides[get_cache] = lambda: DirectCache()
    try:
        response = TestClient(app).get(
            "/api/v1/air-quality", params={"location_id": "new-delhi"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["aqi"]["standard"] == "US EPA AQI"
    assert body["aqi"]["indian_aqi"] is None
    assert body["pollutants"]["pm2_5"] == {
        "value": None,
        "unit": "μg/m³",
        "status": "unavailable",
    }
