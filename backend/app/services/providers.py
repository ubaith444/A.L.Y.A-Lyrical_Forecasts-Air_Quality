import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.errors import ApiError


class OpenMeteoClient:
    def __init__(
        self,
        weather_url: str,
        air_quality_url: str,
        timeout_seconds: float,
        retries: int,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.weather_url = weather_url.rstrip("/")
        self.air_quality_url = air_quality_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.transport = transport

    async def weather(
        self, latitude: float, longitude: float, timezone: str
    ) -> dict[str, Any]:
        return await self._request(
            f"{self.weather_url}/forecast",
            {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "forecast_days": 14,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m",
                "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,precipitation,wind_speed_10m,wind_direction_10m,pressure_msl,cloud_cover,visibility,uv_index",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_direction_10m_dominant,uv_index_max",
            },
        )

    async def forecast(
        self, latitude: float, longitude: float, timezone: str = "Asia/Kolkata", **kwargs
    ) -> dict[str, Any]:
        return await self.weather(latitude=latitude, longitude=longitude, timezone=timezone)

    async def air_quality(
        self, latitude: float, longitude: float, timezone: str
    ) -> dict[str, Any]:
        return await self._request(
            f"{self.air_quality_url}/air-quality",
            {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "current": "european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,sulphur_dioxide",
                "hourly": "european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,sulphur_dioxide",
            },
        )

    async def archive(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        return await self._request(
            "https://archive-api.open-meteo.com/v1/archive",
            {
                "latitude": latitude,
                "longitude": longitude,
                "timezone": timezone,
                "start_date": start_date,
                "end_date": end_date,
                "models": "era5",
                "daily": "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_mean",
            },
        )

    async def archive_hourly(
        self,
        latitude: float,
        longitude: float,
        timezone: str,
        start_date: str,
        end_date: str,
        models: str = "era5_land",
        hourly_variables: list[str] | None = None,
    ) -> dict[str, Any]:
        if not hourly_variables:
            hourly_variables = [
                "temperature_2m",
                "relative_humidity_2m",
                "dew_point_2m",
                "precipitation",
                "wind_speed_10m",
                "wind_direction_10m",
                "surface_pressure",
                "cloud_cover",
            ]
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "start_date": start_date,
            "end_date": end_date,
            "models": models,
            "hourly": ",".join(hourly_variables),
        }
        try:
            return await self._request("https://archive-api.open-meteo.com/v1/archive", params)
        except Exception:
            if models == "era5_land":
                # Fallback to standard ERA5 if era5_land is unavailable for the selected point/dates
                params["models"] = "era5"
                return await self._request("https://archive-api.open-meteo.com/v1/archive", params)
            raise

    async def _request(self, url: str, params: dict) -> dict[str, Any]:
        error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout_seconds),
                    transport=self.transport,
                ) as client:
                    response = await client.get(url, params=params)
                if response.status_code == 429:
                    if attempt < self.retries:
                        await asyncio.sleep(0.2 * (2**attempt))
                        continue
                    raise ApiError(
                        503,
                        "provider_rate_limited",
                        "The weather provider is rate limiting requests. Please try again shortly.",
                    )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or payload.get("error"):
                    raise ValueError("Provider returned an invalid payload")
                return payload
            except ApiError:
                raise
            except (httpx.HTTPError, ValueError) as exc:
                error = exc
                if attempt < self.retries:
                    await asyncio.sleep(0.2 * (2**attempt))
        raise ApiError(
            503,
            "provider_unavailable",
            "The upstream data provider is unavailable.",
            {
                "provider": "Open-Meteo",
                "reason": type(error).__name__ if error else "unknown",
            },
        )


def provenance(provider: str, cached: bool, retrieved_at: datetime) -> dict:
    age_seconds = max(0, round((datetime.now(UTC) - retrieved_at).total_seconds(), 3))
    return {
        "source": provider,
        "retrieved_at": retrieved_at.isoformat(),
        "forecast_issue_time": None,
        "cache": {"hit": cached, "age_seconds": age_seconds},
        "freshness": "fresh",
    }
