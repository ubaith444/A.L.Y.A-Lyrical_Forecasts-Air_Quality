from fastapi.testclient import TestClient

from app.api.dependencies import get_cache, get_provider
from app.main import app


class WeatherProviderMock:
    async def weather(self, **kwargs):
        return {
            "current": {"time": "2026-10-24T12:00", "temperature_2m": 29.5},
            "current_units": {"temperature_2m": "°C"},
            "hourly": {
                "time": [f"2026-10-24T{h:02d}:00" for h in range(24)],
                "temperature_2m": [25.0 + h * 0.2 for h in range(24)],
            },
            "hourly_units": {"temperature_2m": "°C"},
            "daily": {
                "time": ["2026-10-24", "2026-10-25"],
                "temperature_2m_max": [32.0, 31.5],
            },
            "daily_units": {"temperature_2m_max": "°C"},
        }


class CacheMock:
    async def get_or_fetch(self, namespace, params, fetch):
        from datetime import UTC, datetime

        return await fetch(), False, datetime(2026, 10, 24, tzinfo=UTC)


def test_hourly_and_daily_weather_endpoints():
    app.dependency_overrides[get_provider] = lambda: WeatherProviderMock()
    app.dependency_overrides[get_cache] = lambda: CacheMock()
    client = TestClient(app)
    try:
        # Hourly endpoint
        hourly_resp = client.get(
            "/api/v1/weather/hourly", params={"location_id": "new-delhi"}
        )
        assert hourly_resp.status_code == 200
        hourly_data = hourly_resp.json()
        assert "hourly" in hourly_data
        assert len(hourly_data["hourly"]["items"]) == 24
        assert hourly_data["location"]["id"] == "new-delhi"
        assert hourly_data["provenance"]["source"] == "Open-Meteo Forecast API"

        # Daily endpoint
        daily_resp = client.get(
            "/api/v1/weather/daily", params={"location_id": "new-delhi"}
        )
        assert daily_resp.status_code == 200
        daily_data = daily_resp.json()
        assert "daily" in daily_data
        assert len(daily_data["daily"]["items"]) == 2
        assert daily_data["location"]["id"] == "new-delhi"
    finally:
        app.dependency_overrides.clear()
