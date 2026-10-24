from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_cache, get_location_service, get_provider
from app.api.routes.weather import _location
from app.core.errors import ApiError
from app.models.schemas import AirQualityResponse
from app.services.aqi import compute_indian_aqi
from app.services.cache import ResponseCache
from app.services.locations import LocationService
from app.services.providers import OpenMeteoClient, provenance

router = APIRouter()


def _guidance(aqi: int | float | None) -> dict[str, str]:
    if aqi is None:
        return {
            "category": "Unavailable",
            "message": "No verified AQI value is available for health guidance.",
            "standard": "US EPA AQI",
        }
    bands = [
        (50, "Good", "Air quality is satisfactory for most people."),
        (
            100,
            "Moderate",
            "Unusually sensitive people may consider reducing prolonged outdoor exertion.",
        ),
        (
            150,
            "Unhealthy for Sensitive Groups",
            "Sensitive groups may reduce prolonged or heavy outdoor exertion.",
        ),
        (200, "Unhealthy", "People may reduce prolonged or heavy outdoor exertion."),
        (
            300,
            "Very Unhealthy",
            "Consider avoiding prolonged or heavy outdoor exertion.",
        ),
        (500, "Hazardous", "Avoid prolonged outdoor exertion when possible."),
    ]
    for upper, category, message in bands:
        if aqi <= upper:
            return {"category": category, "message": message, "standard": "US EPA AQI"}
    return {
        "category": "Beyond AQI scale",
        "message": "AQI is above the defined scale; follow local public-health advice.",
        "standard": "US EPA AQI",
    }


def _is_number_or_unavailable(value: object) -> bool:
    return value is None or (
        isinstance(value, (int, float)) and not isinstance(value, bool)
    )


@router.get("", response_model=AirQualityResponse)
async def air_quality(
    location_id: str | None = Query(default=None, max_length=100),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    locations: LocationService = Depends(get_location_service),
    client: OpenMeteoClient = Depends(get_provider),
    cache: ResponseCache = Depends(get_cache),
) -> dict:
    location = _location(location_id, latitude, longitude, locations)
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location["timezone"],
    }
    payload, cached, retrieved_at = await cache.get_or_fetch(
        "air_quality", params, lambda: client.air_quality(**params)
    )
    current = payload.get("current")
    if (
        not isinstance(current, dict)
        or not isinstance(current.get("time"), str)
        or not isinstance(payload.get("current_units"), dict)
    ):
        raise ApiError(
            502,
            "provider_invalid_response",
            "The air-quality provider response is missing current readings.",
        )
    pollutants = {
        "pm2_5": current.get("pm2_5"),
        "pm10": current.get("pm10"),
        "nitrogen_dioxide": current.get("nitrogen_dioxide"),
        "ozone": current.get("ozone"),
        "sulphur_dioxide": current.get("sulphur_dioxide"),
        "carbon_monoxide": current.get("carbon_monoxide"),
    }
    us_aqi = current.get("us_aqi")
    european_aqi = current.get("european_aqi")
    if not _is_number_or_unavailable(us_aqi) or not all(
        _is_number_or_unavailable(value) for value in pollutants.values()
    ):
        raise ApiError(
            502,
            "provider_invalid_response",
            "The air-quality provider returned an invalid numeric reading.",
        )
    units = payload["current_units"]
    if any(
        value is not None and not isinstance(units.get(name), str)
        for name, value in pollutants.items()
    ):
        raise ApiError(
            502,
            "provider_invalid_response",
            "The air-quality provider omitted a pollutant unit.",
        )

    hourly = payload.get("hourly")
    indian_calc = compute_indian_aqi(hourly)
    if indian_calc["status"] == "calculated":
        indian_aqi_val = indian_calc["value"]
        indian_aqi_status = "Available: Computed via official CPCB NAQI standard using verified averaging periods."
        health_guidance = {
            "category": indian_calc["category"],
            "message": indian_calc["health_guidance"],
            "standard": "Indian CPCB NAQI",
        }
    else:
        indian_aqi_val = None
        indian_aqi_status = f"Unavailable: {indian_calc['reason']}"
        health_guidance = _guidance(us_aqi)

    return {
        "location": {
            **location,
            "representation": "Values represent the requested coordinate or provider grid cell, not district-wide conditions.",
        },
        "timestamp": current.get("time"),
        "aqi": {
            "value": us_aqi,
            "standard": "US EPA AQI",
            "provider_value": "us_aqi",
            "indian_aqi": indian_aqi_val,
            "indian_aqi_status": indian_aqi_status,
            "european_aqi": european_aqi,
            "cpcb_details": indian_calc if indian_calc["status"] == "calculated" else None,
            "standards_disclaimer": "AQI standards (CPCB NAQI, US EPA, European EAQI) are derived from different breakpoints, averaging periods, and health scales; they are not interchangeable.",
        },
        "pollutants": {
            name: {
                "value": value,
                "unit": payload.get("current_units", {}).get(name),
                "status": "available" if value is not None else "unavailable",
            }
            for name, value in pollutants.items()
        },
        "health_guidance": health_guidance,
        "data_quality": {
            "status": "provider-derived",
            "notes": "Modelled atmospheric composition from Open-Meteo Air Quality API; not direct CPCB monitoring-station readings. AQI standards are not interchangeable.",
        },
        "provenance": provenance("Open-Meteo Air Quality API", cached, retrieved_at),
    }
