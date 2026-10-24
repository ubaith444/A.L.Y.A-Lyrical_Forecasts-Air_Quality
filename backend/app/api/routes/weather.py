from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_cache, get_location_service, get_provider
from app.core.errors import ApiError
from app.models.schemas import (
    CurrentWeatherResponse,
    DailyWeatherResponse,
    HourlyWeatherResponse,
    WeatherResponse,
)
from app.services.cache import ResponseCache
from app.services.locations import LocationService
from app.services.providers import OpenMeteoClient, provenance

router = APIRouter()


def _location(
    location_id: str | None,
    latitude: float | None,
    longitude: float | None,
    service: LocationService,
) -> dict:
    if location_id:
        if latitude is not None or longitude is not None:
            raise ApiError(
                422,
                "ambiguous_location",
                "Use either location_id or latitude and longitude, not both.",
            )
        return service.get(location_id)
    if latitude is None or longitude is None:
        raise ApiError(
            422,
            "location_required",
            "Provide location_id or both latitude and longitude.",
        )
    return {
        "id": None,
        "name": None,
        "state": None,
        "type": "coordinate",
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "Asia/Kolkata",
    }


def _series(block: dict, limit: int) -> list[dict]:
    times = block.get("time")
    if not isinstance(times, list):
        raise ApiError(
            502,
            "provider_invalid_response",
            "The weather provider returned no time series.",
        )
    records = []
    for index, timestamp in enumerate(times[:limit]):
        record = {"time": timestamp}
        for key, values in block.items():
            if key != "time" and isinstance(values, list) and index < len(values):
                record[key] = values[index]
        records.append(record)
    return records


def _validate_weather_payload(payload: dict) -> None:
    current = payload.get("current")
    hourly = payload.get("hourly")
    daily = payload.get("daily")
    if (
        not isinstance(current, dict)
        or not isinstance(hourly, dict)
        or not isinstance(daily, dict)
        or not all(
            isinstance(payload.get(key), dict)
            for key in ("current_units", "hourly_units", "daily_units")
        )
    ):
        raise ApiError(
            502,
            "provider_invalid_response",
            "The weather provider response is missing expected forecast fields.",
        )
    if not isinstance(current.get("time"), str):
        raise ApiError(
            502,
            "provider_invalid_response",
            "The weather provider returned an invalid current-weather timestamp.",
        )
    if any(
        value is not None
        and (not isinstance(value, (int, float)) or isinstance(value, bool))
        for key, value in current.items()
        if key != "time"
    ):
        raise ApiError(
            502,
            "provider_invalid_response",
            "The weather provider returned an invalid current-weather value.",
        )
    for name, block in (("hourly", hourly), ("daily", daily)):
        times = block.get("time")
        if (
            not isinstance(times, list)
            or not times
            or not all(isinstance(value, str) for value in times)
        ):
            raise ApiError(
                502,
                "provider_invalid_response",
                f"The weather provider returned an invalid {name} time series.",
            )
        for key, values in block.items():
            if key == "time":
                continue
            if not isinstance(values, list) or len(values) != len(times):
                raise ApiError(
                    502,
                    "provider_invalid_response",
                    f"The weather provider returned a malformed {name} variable.",
                )
            if key in {"sunrise", "sunset"}:
                valid = all(value is None or isinstance(value, str) for value in values)
            else:
                valid = all(
                    value is None
                    or (isinstance(value, (int, float)) and not isinstance(value, bool))
                    for value in values
                )
            if not valid:
                raise ApiError(
                    502,
                    "provider_invalid_response",
                    f"The weather provider returned an invalid {name} value.",
                )


async def _forecast(
    location: dict, client: OpenMeteoClient, cache: ResponseCache
) -> dict:
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location["timezone"],
    }
    payload, cached, retrieved_at = await cache.get_or_fetch(
        "weather", params, lambda: client.weather(**params)
    )
    _validate_weather_payload(payload)
    return {
        "location": {
            **location,
            "representation": "Forecast values represent the requested coordinate or provider grid cell, not district-wide conditions.",
        },
        "current": {
            "time": payload["current"].get("time"),
            "values": {
                key: value for key, value in payload["current"].items() if key != "time"
            },
            "units": payload.get("current_units", {}),
        },
        "hourly": {
            "items": _series(payload["hourly"], 72),
            "units": payload.get("hourly_units", {}),
        },
        "daily": {
            "items": _series(payload["daily"], 14),
            "units": payload.get("daily_units", {}),
        },
        "provenance": provenance("Open-Meteo Forecast API", cached, retrieved_at),
    }


@router.get("", response_model=WeatherResponse)
async def weather(
    location_id: str | None = Query(default=None, max_length=100),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    locations: LocationService = Depends(get_location_service),
    client: OpenMeteoClient = Depends(get_provider),
    cache: ResponseCache = Depends(get_cache),
) -> dict:
    return await _forecast(
        _location(location_id, latitude, longitude, locations), client, cache
    )


@router.get("/current", response_model=CurrentWeatherResponse)
async def current_weather(
    location_id: str | None = Query(default=None, max_length=100),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    locations: LocationService = Depends(get_location_service),
    client: OpenMeteoClient = Depends(get_provider),
    cache: ResponseCache = Depends(get_cache),
) -> dict:
    forecast = await _forecast(
        _location(location_id, latitude, longitude, locations), client, cache
    )
    return {key: forecast[key] for key in ("location", "current", "provenance")}


@router.get("/hourly", response_model=HourlyWeatherResponse)
async def hourly_weather(
    location_id: str | None = Query(default=None, max_length=100),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    locations: LocationService = Depends(get_location_service),
    client: OpenMeteoClient = Depends(get_provider),
    cache: ResponseCache = Depends(get_cache),
) -> dict:
    forecast = await _forecast(
        _location(location_id, latitude, longitude, locations), client, cache
    )
    return {key: forecast[key] for key in ("location", "hourly", "provenance")}


@router.get("/daily", response_model=DailyWeatherResponse)
async def daily_weather(
    location_id: str | None = Query(default=None, max_length=100),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    locations: LocationService = Depends(get_location_service),
    client: OpenMeteoClient = Depends(get_provider),
    cache: ResponseCache = Depends(get_cache),
) -> dict:
    forecast = await _forecast(
        _location(location_id, latitude, longitude, locations), client, cache
    )
    return {key: forecast[key] for key in ("location", "daily", "provenance")}

