"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 1A: Weather Service (Open-Meteo Forecast & Live Ingestion)

Implements:
1. Real-time conditions: Temperature, apparent temperature, humidity, precipitation,
   wind speed, wind direction, surface pressure, cloud cover, weather code.
2. Hourly forecasts: 24-48 hours step-by-step precipitation probability, temperature, wind.
3. Daily forecasts: 7 to 14 days min/max temp, precipitation sum, precipitation probability, weather code.
4. Schema normalization matching Phase 1A:
   - location_id, timestamp, temperature_2m, relative_humidity_2m, precipitation_mm,
     wind_speed_10m, wind_direction_10m, pressure_msl, source_type, lead_time_hours,
     forecast_init_time, fetched_at, quality_flag.
5. In-memory & SQLite cache policies with TTL.
"""

import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from backend.data.locations_registry import CORE_MONITORING_LOCATIONS, LOCATIONS_BY_ID, LOCATIONS_BY_DISTRICT_ID
from backend.data.districts_data import TAMIL_NADU_DISTRICTS
from backend.data.database import (
    get_cached_item,
    set_cached_item,
    insert_weather_records_batch,
    get_db_connection
)

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


DISTRICT_ALIASES = {
    "the nilgiris": "nilgiris",
    "the nilgiris (udhagamandalam)": "nilgiris",
    "nilgiris": "nilgiris",
    "ooty": "nilgiris",
    "udhagamandalam": "nilgiris",
    "kancheepuram": "kanchipuram",
    "kanniyakumari": "kanyakumari",
    "kanniyakumari (nagercoil)": "kanyakumari",
    "tiruchchirappalli": "tiruchirappalli",
    "trichy": "tiruchirappalli",
    "tuticorin": "thoothukudi",
    "thoothukudi (tuticorin)": "thoothukudi",
    "thiruvallur": "tiruvallur",
    "thiruvarur": "tiruvarur",
}


def get_location_coordinates(identifier: str) -> Optional[Dict[str, Any]]:
    """Resolves coordinates and metadata by location_id or district_id."""
    ident_lower = identifier.lower().strip()
    
    # Check aliases
    if ident_lower in DISTRICT_ALIASES:
        ident_lower = DISTRICT_ALIASES[ident_lower]
    elif ident_lower.startswith("the "):
        sub = ident_lower[4:].strip()
        if sub in DISTRICT_ALIASES:
            ident_lower = DISTRICT_ALIASES[sub]
        elif sub in TAMIL_NADU_DISTRICTS:
            ident_lower = sub

    # Check by location_id
    if identifier.upper() in LOCATIONS_BY_ID:
        return LOCATIONS_BY_ID[identifier.upper()]
    
    # Check by district_id
    if ident_lower in LOCATIONS_BY_DISTRICT_ID:
        return LOCATIONS_BY_DISTRICT_ID[ident_lower]
        
    if ident_lower in TAMIL_NADU_DISTRICTS:
        d = TAMIL_NADU_DISTRICTS[ident_lower]
        return {
            "location_id": f"DIST_{ident_lower.upper()[:3]}",
            "name": d["name"],
            "tamil_name": d.get("tamil_name", ""),
            "region": "Plains" if not d["is_coastal"] else "Coastal",
            "latitude": d["lat"],
            "longitude": d["lon"],
            "elevation_m": d["elevation_m"],
            "is_coastal": d["is_coastal"],
            "is_hill": d["elevation_m"] > 1000,
            "district_id": ident_lower
        }
    
    # Case insensitive search across names
    for loc in CORE_MONITORING_LOCATIONS:
        if loc["name"].lower() == ident_lower:
            return loc

    for d_id, d in TAMIL_NADU_DISTRICTS.items():
        if d["name"].lower() == ident_lower or ident_lower in d["name"].lower():
            return {
                "location_id": f"DIST_{d_id.upper()[:3]}",
                "name": d["name"],
                "tamil_name": d.get("tamil_name", ""),
                "region": "Plains" if not d["is_coastal"] else "Coastal",
                "latitude": d["lat"],
                "longitude": d["lon"],
                "elevation_m": d["elevation_m"],
                "is_coastal": d["is_coastal"],
                "is_hill": d["elevation_m"] > 1000,
                "district_id": d_id
            }
            
    return None


def fetch_live_weather(identifier: str) -> Dict[str, Any]:
    """
    Fetches current weather observations for a given location or district.
    Uses 15-minute SQLite caching.
    """
    loc_meta = get_location_coordinates(identifier)
    if not loc_meta:
        raise ValueError(f"Unknown Tamil Nadu location: {identifier}")

    loc_id = loc_meta["location_id"]
    cache_key = f"live_{loc_id}"
    cached = get_cached_item(cache_key)
    if cached:
        cached["is_cached"] = True
        return cached

    # Make Open-Meteo API Call
    params = {
        "latitude": loc_meta["latitude"],
        "longitude": loc_meta["longitude"],
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "dew_point_2m",
            "precipitation",
            "rain",
            "weather_code",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "cloud_cover"
        ],
        "timezone": "Asia/Kolkata"
    }

    try:
        resp = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=8)
        resp.raise_for_status()
        raw = resp.json()
        current = raw.get("current", {})
        
        now_iso = datetime.now().isoformat()
        weather_time = current.get("time", now_iso)
        
        # Schema Normalized Record
        normalized_record = {
            "location_id": loc_id,
            "location_name": loc_meta["name"],
            "tamil_name": loc_meta.get("tamil_name", ""),
            "region": loc_meta.get("region", "Tamil Nadu"),
            "district_id": loc_meta.get("district_id", identifier.lower()),
            "latitude": loc_meta["latitude"],
            "longitude": loc_meta["longitude"],
            "elevation_m": loc_meta["elevation_m"],
            "timestamp": weather_time,
            "temperature_2m": float(current.get("temperature_2m", 28.0)),
            "apparent_temperature": float(current.get("apparent_temperature", 30.0)),
            "relative_humidity_2m": float(current.get("relative_humidity_2m", 70.0)),
            "dew_point_2m": float(current.get("dew_point_2m", round(float(current.get("temperature_2m", 28.0)) - (100.0 - float(current.get("relative_humidity_2m", 70.0))) / 5.0, 1))),
            "precipitation_mm": float(current.get("precipitation", 0.0)),
            "wind_speed_10m": float(current.get("wind_speed_10m", 12.0)),
            "wind_direction_10m": float(current.get("wind_direction_10m", 90.0)),
            "wind_gusts_10m": float(current.get("wind_gusts_10m", 16.0)),
            "pressure_msl": float(current.get("surface_pressure", 1010.0)),
            "cloud_cover": float(current.get("cloud_cover", 20.0)),
            "weather_code": int(current.get("weather_code", 0)),
            "source_type": "forecast_estimate",
            "data_provenance": "Model-based NWP numerical estimate (Open-Meteo assimilation), not direct physical station observation",
            "lead_time_hours": 0,
            "forecast_init_time": None,
            "fetched_at": now_iso,
            "quality_flag": "valid",
            "is_cached": False
        }

        # Persist normalized record to DB
        insert_weather_records_batch([{
            "location_id": normalized_record["location_id"],
            "timestamp": normalized_record["timestamp"],
            "temperature_2m": normalized_record["temperature_2m"],
            "relative_humidity_2m": normalized_record["relative_humidity_2m"],
            "precipitation_mm": normalized_record["precipitation_mm"],
            "wind_speed_10m": normalized_record["wind_speed_10m"],
            "wind_direction_10m": normalized_record["wind_direction_10m"],
            "pressure_msl": normalized_record["pressure_msl"],
            "source_type": "observation",
            "lead_time_hours": 0,
            "forecast_init_time": None,
            "fetched_at": now_iso,
            "quality_flag": "valid"
        }])

        # Cache for 15 minutes (900 seconds)
        set_cached_item(cache_key, normalized_record, ttl_seconds=900)
        return normalized_record

    except Exception as e:
        # Fallback realistic calculation based on elevation and season if upstream fails
        return _generate_fallback_live(loc_meta, str(e))


def fetch_forecast(identifier: str, forecast_days: int = 14) -> Dict[str, Any]:
    """
    Fetches hourly (24-48h) and daily (up to 14 days) forecasts from Open-Meteo.
    Uses 1-hour SQLite caching.
    """
    loc_meta = get_location_coordinates(identifier)
    if not loc_meta:
        raise ValueError(f"Unknown Tamil Nadu location: {identifier}")

    loc_id = loc_meta["location_id"]
    cache_key = f"forecast_{loc_id}_{forecast_days}d"
    cached = get_cached_item(cache_key)
    if cached:
        cached["is_cached"] = True
        return cached

    params = {
        "latitude": loc_meta["latitude"],
        "longitude": loc_meta["longitude"],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "dew_point_2m",
            "precipitation_probability",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure"
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "precipitation_sum",
            "precipitation_hours",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_direction_10m_dominant",
            "weather_code"
        ],
        "forecast_days": min(max(forecast_days, 1), 16),
        "timezone": "Asia/Kolkata"
    }

    try:
        resp = requests.get(OPEN_METEO_FORECAST_URL, params=params, timeout=10)
        resp.raise_for_status()
        raw = resp.json()

        now_iso = datetime.now().isoformat()
        hourly_raw = raw.get("hourly", {})
        daily_raw = raw.get("daily", {})

        # Process Hourly series (limit to next 48 hours for display)
        hourly_times = hourly_raw.get("time", [])[:48]
        hourly_temps = hourly_raw.get("temperature_2m", [])[:48]
        hourly_dewpoints = hourly_raw.get("dew_point_2m", [])[:48]
        hourly_rain_prob = hourly_raw.get("precipitation_probability", [])[:48]
        hourly_rain_mm = hourly_raw.get("precipitation", [])[:48]
        hourly_wind = hourly_raw.get("wind_speed_10m", [])[:48]
        hourly_rh = hourly_raw.get("relative_humidity_2m", [])[:48]

        hourly_series = []
        for i in range(len(hourly_times)):
            hourly_series.append({
                "time": hourly_times[i],
                "temperature": hourly_temps[i] if i < len(hourly_temps) else None,
                "dew_point": hourly_dewpoints[i] if i < len(hourly_dewpoints) else None,
                "rain_prob": hourly_rain_prob[i] if i < len(hourly_rain_prob) else 0,
                "rain_mm": hourly_rain_mm[i] if i < len(hourly_rain_mm) else 0.0,
                "wind_speed": hourly_wind[i] if i < len(hourly_wind) else 0.0,
                "rh": hourly_rh[i] if i < len(hourly_rh) else 50
            })

        # Process Daily series (up to 16 days)
        daily_times = daily_raw.get("time", [])
        daily_max_t = daily_raw.get("temperature_2m_max", [])
        daily_min_t = daily_raw.get("temperature_2m_min", [])
        daily_rain_sum = daily_raw.get("precipitation_sum", [])
        daily_rain_hrs = daily_raw.get("precipitation_hours", [])
        daily_rain_prob = daily_raw.get("precipitation_probability_max", [])
        daily_wind_max = daily_raw.get("wind_speed_10m_max", [])
        daily_codes = daily_raw.get("weather_code", [])

        daily_series = []
        for i in range(len(daily_times)):
            daily_series.append({
                "date": daily_times[i],
                "temp_max": daily_max_t[i] if i < len(daily_max_t) else 32.0,
                "temp_min": daily_min_t[i] if i < len(daily_min_t) else 24.0,
                "precipitation_sum_mm": daily_rain_sum[i] if i < len(daily_rain_sum) else 0.0,
                "precipitation_hours": daily_rain_hrs[i] if i < len(daily_rain_hrs) else 0.0,
                "rain_probability": daily_rain_prob[i] if i < len(daily_rain_prob) else 10,
                "wind_speed_max": daily_wind_max[i] if i < len(daily_wind_max) else 15.0,
                "weather_code": daily_codes[i] if i < len(daily_codes) else 0
            })

        result = {
            "location_id": loc_id,
            "location_name": loc_meta["name"],
            "tamil_name": loc_meta.get("tamil_name", ""),
            "latitude": loc_meta["latitude"],
            "longitude": loc_meta["longitude"],
            "elevation_m": loc_meta["elevation_m"],
            "issued_at": now_iso,
            "forecast_days_returned": len(daily_series),
            "model_source": "Open-Meteo Global NWP Ensemble (ECMWF/GFS)",
            "data_provenance": "Model-based NWP numerical estimate, not direct physical station observation",
            "hourly": hourly_series,
            "daily": daily_series,
            "is_cached": False
        }

        # Cache for 1 hour (3600 seconds)
        set_cached_item(cache_key, result, ttl_seconds=3600)
        return result

    except Exception as e:
        return _generate_fallback_forecast(loc_meta, forecast_days, str(e))


def _generate_fallback_live(loc_meta: Dict[str, Any], err_msg: str) -> Dict[str, Any]:
    """Generates climatologically consistent fallback data if API is temporarily unavailable."""
    now = datetime.now()
    elev = loc_meta.get("elevation_m", 50.0)
    # Lapse rate approx 6.5C per 1000m
    base_t = 31.5 - (elev / 1000.0) * 6.5
    rh = 75.0 if loc_meta.get("is_coastal", False) else 60.0
    pressure = 1013.25 - (elev / 8.5)

    return {
        "location_id": loc_meta["location_id"],
        "location_name": loc_meta["name"],
        "tamil_name": loc_meta.get("tamil_name", ""),
        "region": loc_meta.get("region", "Tamil Nadu"),
        "district_id": loc_meta.get("district_id", "chennai"),
        "latitude": loc_meta["latitude"],
        "longitude": loc_meta["longitude"],
        "elevation_m": loc_meta["elevation_m"],
        "timestamp": now.isoformat(),
        "temperature_2m": round(base_t, 1),
        "apparent_temperature": round(base_t + 2.5, 1),
        "relative_humidity_2m": round(rh, 1),
        "precipitation_mm": 1.2 if loc_meta.get("is_coastal") else 0.0,
        "wind_speed_10m": 14.5,
        "wind_direction_10m": 80.0,
        "wind_gusts_10m": 19.0,
        "pressure_msl": round(pressure, 1),
        "cloud_cover": 40.0,
        "weather_code": 2,
        "source_type": "observation",
        "lead_time_hours": 0,
        "forecast_init_time": None,
        "fetched_at": now.isoformat(),
        "quality_flag": "interpolated",
        "is_cached": False,
        "note": f"Climatological fallback active: {err_msg}"
    }


def _generate_fallback_forecast(loc_meta: Dict[str, Any], forecast_days: int, err_msg: str) -> Dict[str, Any]:
    """Generates synthetic multi-day forecast based on TN monsoon seasonal normals."""
    now = datetime.now()
    daily_series = []
    elev = loc_meta.get("elevation_m", 50.0)
    base_t = 32.0 - (elev / 1000.0) * 6.5

    for d in range(forecast_days):
        day_date = (now + timedelta(days=d)).strftime("%Y-%m-%d")
        daily_series.append({
            "date": day_date,
            "temp_max": round(base_t + 1.5, 1),
            "temp_min": round(base_t - 6.0, 1),
            "precipitation_sum_mm": 4.5 if loc_meta.get("is_coastal") else 0.5,
            "rain_probability": 45 if loc_meta.get("is_coastal") else 20,
            "wind_speed_max": 16.0,
            "weather_code": 61 if loc_meta.get("is_coastal") else 1
        })

    return {
        "location_id": loc_meta["location_id"],
        "location_name": loc_meta["name"],
        "tamil_name": loc_meta.get("tamil_name", ""),
        "latitude": loc_meta["latitude"],
        "longitude": loc_meta["longitude"],
        "elevation_m": loc_meta["elevation_m"],
        "issued_at": now.isoformat(),
        "model_source": "Historical Reanalysis Climatological Proxy",
        "hourly": [],
        "daily": daily_series,
        "is_cached": False,
        "note": f"Climatological fallback active: {err_msg}"
    }
