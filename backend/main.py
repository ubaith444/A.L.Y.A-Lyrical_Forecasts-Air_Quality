"""
Tamil Nadu Climate & Forecast Intelligence Platform
FastAPI Server & Central Intelligence Controller

Exposes comprehensive REST API:
- /api/districts: All 38 Tamil Nadu districts & metadata
- /api/locations: 16 Core monitoring locations
- /api/weather/live/{district_id}: Live meteorological conditions
- /api/weather/forecast/{district_id}: 7-14 day NWP forecasts (Open-Meteo)
- /api/weather/predict/{district_id}: In-house ML model inference
- /api/weather/compare/{district_id}: Dual-Engine side-by-side comparison
- /api/climate/historical/{district_id}: IMD monsoon analytics & departure
- /api/risks: Statewide 38-district risk matrix
- /api/backtest/{district_id}: Forecast accuracy & backtest evaluation
- /api/insights/generate: AI natural language summary
"""

import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional

from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.data.districts_data import TAMIL_NADU_DISTRICTS, TN_MAJOR_RESERVOIRS
from backend.data.locations_registry import CORE_MONITORING_LOCATIONS
from backend.data.database import (
    init_db,
    get_cached_item,
    set_cached_item,
    get_climate_report,
    get_data_dir,
    get_db_path,
    get_models_dir,
    get_datasets_dir,
    get_db_connection,
    backup_database
)
from backend.services.weather_service import fetch_live_weather, fetch_forecast
from backend.models.predictor import predictor
from backend.services.climate_analytics import get_district_climate_analytics
from backend.services.phase3_climate_analytics import (
    get_historical_trends,
    get_seasonal_rainfall,
    get_climate_anomalies,
    compare_district_climates,
    get_climate_summary,
    generate_climate_report
)
from backend.services.phase4_ml_pipeline import (
    get_ml_experiments_summary,
    get_ml_models_registry,
    get_live_ml_forecast,
    get_backtest_eval_series,
    get_timesfm_operational_benchmark,
    execute_chronological_backtest
)
from backend.services.risk import (
    APPLICATION_THRESHOLDS,
    IMD_WARNING_CRITERIA,
    get_threshold_config,
    get_official_imd_warnings,
    evaluate_statewide_risk_overview,
    get_all_district_risk_summaries,
    get_single_district_bilingual_summary,
    get_alerts_list,
    get_alert_by_id,
    acknowledge_alert,
    export_alerts_to_csv_string
)
from backend.services.impact_engine import evaluate_sector_impacts, get_statewide_risk_matrix
from backend.services.backtesting_engine import run_historical_backtest
from backend.services.ai_insights import generate_climate_ai_insight
from backend.services.guidance import generate_meteorological_guidance
from backend.services.impact import (
    evaluate_district_sector_matrix,
    get_all_districts_sector_matrix,
    export_sector_matrix_to_csv_string
)
from backend.services.settings import (
    get_data_sources_list,
    update_data_source_status,
    get_operational_settings,
    update_operational_setting,
    get_operational_audit_log,
    check_data_sources_health
)

# Initialize SQLite database schema
init_db()

app = FastAPI(
    title="Tamil Nadu Climate & Forecast Intelligence API",
    description="High-precision meteorological analytics, dual-engine prediction, and multi-sector risk intelligence for Tamil Nadu.",
    version="1.0.0"
)

# Production CORS configuration
frontend_origin = os.environ.get("FRONTEND_ORIGIN")
app_env = os.environ.get("APP_ENV", "development").lower()

if app_env == "production" and frontend_origin:
    # Strict production origin control (Checklist item E: Allow only the frontend's production origin)
    allowed_origins = [frontend_origin.rstrip("/")]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Liveness probe: verifies service liveness and storage paths."""
    db_p = get_db_path()
    return {
        "status": "HEALTHY",
        "service": "Tamil Nadu Climate & Forecast Intelligence Platform",
        "version": "1.0.0",
        "environment": os.environ.get("APP_ENV", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "storage": {
            "data_dir": get_data_dir(),
            "db_path": db_p,
            "db_exists": os.path.exists(db_p),
            "models_dir": get_models_dir(),
            "datasets_dir": get_datasets_dir()
        },
        "districts_monitored": len(TAMIL_NADU_DISTRICTS),
        "monitoring_stations": len(CORE_MONITORING_LOCATIONS),
        "ml_model_loaded": predictor.clf_rain is not None
    }


@app.get("/ready")
def readiness_check():
    """Readiness probe: validates SQLite connectivity, table records, and ML model availability."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM locations")
        loc_count = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database readiness check failed: {str(e)}")

    ml_ready = predictor is not None and predictor.clf_rain is not None
    if not ml_ready:
        raise HTTPException(status_code=503, detail="ML inference engine not ready.")

    return {
        "ready": True,
        "database": "CONNECTED",
        "locations_count": loc_count,
        "ml_predictor_ready": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/backup")
def trigger_sqlite_backup():
    """Triggers an atomic SQLite online backup without copying a live database blindly."""
    try:
        result = backup_database()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database backup failed: {str(e)}")


@app.get("/api/districts")
def list_districts():
    """Returns list of all 38 Tamil Nadu districts with geo-climatological metadata."""
    dist_list = []
    for d_id, d in TAMIL_NADU_DISTRICTS.items():
        dist_list.append({
            "id": d_id,
            "name": d["name"],
            "tamil_name": d.get("tamil_name", ""),
            "lat": d["lat"],
            "lon": d["lon"],
            "elevation_m": d["elevation_m"],
            "is_coastal": d["is_coastal"],
            "is_hill": d["elevation_m"] > 1000,
            "region": "Western Ghats" if d["elevation_m"] > 1000 else ("Coastal Corridor" if d["is_coastal"] else "Interior Plains"),
            "normal_annual_rainfall_mm": d.get("normal_annual_rainfall_mm", 950.0),
            "nem_normal_mm": d.get("nem_normal_mm", 450.0),
            "swm_normal_mm": d.get("swm_normal_mm", 320.0),
            "primary_crops": d.get("primary_crops", []),
            "critical_reservoirs": d.get("critical_reservoirs", []),
            "agriculture_impact": d.get("agriculture_impact", "")
        })
    # Sort by name
    return sorted(dist_list, key=lambda x: x["name"])


@app.get("/api/locations")
def list_monitoring_locations():
    """Returns the 16 prioritized Phase 1A monitoring locations across 6 regions."""
    return CORE_MONITORING_LOCATIONS


@app.get("/api/reservoirs")
def list_reservoirs():
    """Returns major Tamil Nadu reservoirs and monitored capacities."""
    return TN_MAJOR_RESERVOIRS


@app.get("/api/weather/live/{district_id}")
def get_live_weather(district_id: str):
    """Fetches real-time weather observations for a district or location."""
    try:
        return fetch_live_weather(district_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/weather/current")
def get_current_weather(district: str = Query(default="chennai", description="District or Location name/ID")):
    """
    Phase 2 API: Current weather summary including 6 KPI values, UV index,
    today's min/max and sunrise/sunset, and meteorological status flags.
    Cached for 10 minutes.
    """
    cache_key = f"current_weather_{district.lower().strip()}"
    cached = get_cached_item(cache_key)
    if cached:
        return cached

    try:
        live = fetch_live_weather(district)
        # Fetch today's summary from forecast
        try:
            fc = fetch_forecast(district, forecast_days=1)
            today = fc.get("daily", [{}])[0]
        except Exception:
            today = {}

        # Cloud cover & UV Index estimate
        cloud = live.get("cloud_cover", 20.0)
        temp = live.get("temperature_2m", 30.0)
        rain = live.get("precipitation_mm", 0.0)
        wind = live.get("wind_speed_10m", 10.0)

        # Realistic UV index estimation for tropical latitude (13°N)
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 18:
            hour_factor = max(0.0, 1.0 - abs(current_hour - 12.5) / 6.0)
            uv_index = round(9.0 * hour_factor * (1.0 - 0.7 * (cloud / 100.0)), 1)
        else:
            uv_index = 0.0

        # Status categorization
        if rain >= 15.0 or wind >= 40.0:
            status = "Storm Risk"
            status_desc = "High wind and intense rainfall alerts active"
        elif rain > 0.0:
            status = "Rainy"
            status_desc = f"Active showers: {rain:.1f} mm recorded"
        elif temp >= 38.0:
            status = "Hot"
            status_desc = f"Severe thermal exposure: {temp:.1f}°C"
        elif cloud >= 60.0:
            status = "Cloudy"
            status_desc = f"Overcast skies ({cloud:.0f}% coverage)"
        else:
            status = "Clear"
            status_desc = "Clear and sunny tropical conditions"

        # Stale data calculation
        fetched_at = live.get("fetched_at", datetime.now().isoformat())
        try:
            diff_min = (datetime.now() - datetime.fromisoformat(fetched_at.split("+")[0])).total_seconds() / 60.0
            is_stale = diff_min > 45.0
        except Exception:
            is_stale = False
            diff_min = 5.0

        result = {
            **live,
            "uv_index": uv_index,
            "status": status,
            "status_description": status_desc,
            "is_stale": is_stale,
            "data_freshness_minutes": round(diff_min, 1),
            "today_summary": {
                "temp_max": today.get("temp_max", round(temp + 2.5, 1)),
                "temp_min": today.get("temp_min", round(temp - 4.0, 1)),
                "expected_rain_mm": today.get("precipitation_sum_mm", rain),
                "rain_probability": today.get("rain_probability", 20),
                "sunrise": "06:04 AM",
                "sunset": "06:08 PM"
            }
        }
        set_cached_item(cache_key, result, ttl_seconds=600)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/weather/hourly")
def get_hourly_weather(
    district: str = Query(default="chennai"),
    hours: int = Query(default=48, ge=12, le=72)
):
    """
    Phase 2 API: 24–48 hour timeline with temperature, feels-like, separate rainfall mm
    and rain probability %, humidity, wind, weather condition icons, and hazard highlights.
    """
    try:
        fc = fetch_forecast(district, forecast_days=3)
        hourly_list = fc.get("hourly", [])[:hours]

        enriched_hourly = []
        for h in hourly_list:
            t = h.get("temperature", 28.0)
            rain_mm = h.get("rain_mm", 0.0)
            rain_prob = h.get("rain_prob", 0)
            time_str = h.get("time", "")

            # Determine day/night from hour
            try:
                hour_int = int(time_str.split("T")[1].split(":")[0])
                is_day = 6 <= hour_int <= 18
            except Exception:
                is_day = True
                hour_int = 12

            # Weather icon and condition
            if rain_mm >= 10.0:
                condition = "Heavy Rain"
                icon = "cloud-rain"
            elif rain_mm > 0.0 or rain_prob >= 50:
                condition = "Showers"
                icon = "cloud-drizzle"
            elif t >= 38.0:
                condition = "Intense Heat"
                icon = "sun-heat"
            elif is_day:
                condition = "Sunny" if h.get("cloud_cover", 20) < 40 else "Partly Cloudy"
                icon = "sun" if h.get("cloud_cover", 20) < 40 else "cloud-sun"
            else:
                condition = "Clear Night"
                icon = "moon"

            enriched_hourly.append({
                "time": time_str,
                "hour_label": f"{hour_int:02d}:00",
                "temperature": t,
                "apparent_temperature": round(t + (1.5 if t > 28 else -0.5), 1),
                "rain_mm": rain_mm,
                "precipitation_probability_pct": rain_prob,
                "humidity": h.get("humidity", 70),
                "wind_speed": h.get("wind_speed", 12.0),
                "dew_point": h.get("dew_point", 22.0),
                "condition": condition,
                "icon": icon,
                "is_day": is_day,
                "is_heavy_rain": rain_mm >= 15.0 or rain_prob >= 75,
                "is_high_temp": t >= 38.0
            })

        return {
            "district": district,
            "hours_count": len(enriched_hourly),
            "forecast_horizon": f"Next {len(enriched_hourly)} Hours",
            "hourly": enriched_hourly
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/weather/daily")
def get_daily_weather(
    district: str = Query(default="chennai"),
    days: int = Query(default=14, ge=7, le=16)
):
    """
    Phase 2 API: 7 to 14 day synoptic forecast cards with min/max temp,
    separate rainfall amount and probability, warnings, and day-over-day trends.
    """
    try:
        fc = fetch_forecast(district, forecast_days=days)
        daily_list = fc.get("daily", [])

        # Enrich daily list with warnings and delta against previous day
        enriched_daily = []
        for i, d in enumerate(daily_list):
            t_max = d.get("temp_max", 32.0)
            t_min = d.get("temp_min", 24.0)
            rain_mm = d.get("precipitation_sum_mm", 0.0)
            rain_prob = d.get("rain_probability", 10)

            # Warning flags
            warnings = []
            if t_max >= 40.0:
                warnings.append("Severe Heatwave Alert (IMD Criteria)")
            elif t_max >= 38.0:
                warnings.append("Elevated Heat Alert")
            if rain_mm >= 64.5:
                warnings.append("Heavy Rainfall Warning (IMD Yellow/Orange Alert)")
            elif rain_mm >= 25.0:
                warnings.append("Moderate Rainfall Expected")

            # Day-over-day comparison
            if i > 0:
                prev = daily_list[i - 1]
                temp_change = round(t_max - prev.get("temp_max", t_max), 1)
                rain_change = round(rain_mm - prev.get("precipitation_sum_mm", rain_mm), 1)
            else:
                temp_change = 0.0
                rain_change = 0.0

            enriched_daily.append({
                **d,
                "day_number": i + 1,
                "has_warning": len(warnings) > 0,
                "warnings": warnings,
                "temp_change_from_prev": temp_change,
                "rain_change_from_prev": rain_change,
                "thermal_range": round(t_max - t_min, 1)
            })

        return {
            "district": district,
            "days_count": len(enriched_daily),
            "provider_horizon": "Open-Meteo ECMWF/GFS Operational Ensemble",
            "daily": enriched_daily
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/districts/compare")
def compare_multiple_districts(
    names: str = Query(default="Chennai,Coimbatore,Madurai,Salem", description="Comma-separated district names (up to 4)")
):
    """
    Phase 2 API: Side-by-side comparison of up to 4 Tamil Nadu districts:
    Current temperature, rainfall, humidity, wind, and ranking by hottest, wettest, and windiest.
    """
    raw_names = [n.strip() for n in names.split(",") if n.strip()][:4]
    if not raw_names:
        raw_names = ["chennai", "coimbatore"]

    def fetch_single_compared(d_name):
        try:
            live = fetch_live_weather(d_name)
            d_key = live.get("district_id", d_name.lower())
            dist_meta = TAMIL_NADU_DISTRICTS.get(d_key, {})
            return {
                "district_id": d_key,
                "name": live.get("location_name", d_name.title()),
                "tamil_name": live.get("tamil_name", ""),
                "region": live.get("region", "Interior"),
                "elevation_m": live.get("elevation_m", 10),
                "temperature_2m": live.get("temperature_2m", 30.0),
                "apparent_temperature": live.get("apparent_temperature", 32.0),
                "relative_humidity_2m": live.get("relative_humidity_2m", 65.0),
                "precipitation_mm": live.get("precipitation_mm", 0.0),
                "wind_speed_10m": live.get("wind_speed_10m", 12.0),
                "pressure_msl": live.get("pressure_msl", 1010.0),
                "cloud_cover": live.get("cloud_cover", 20.0),
                "normal_annual_rainfall_mm": dist_meta.get("normal_annual_rainfall_mm", 950.0),
                "is_coastal": dist_meta.get("is_coastal", False),
                "is_hill": dist_meta.get("elevation_m", 0) > 1000
            }
        except Exception as e:
            # Graceful error handling for missing/unconfigured districts
            return {
                "district_id": d_name.lower(),
                "name": d_name.title(),
                "error": f"Data temporarily unavailable: {str(e)}"
            }

    with ThreadPoolExecutor(max_workers=min(4, len(raw_names))) as executor:
        compared_districts = list(executor.map(fetch_single_compared, raw_names))

    # Rankings
    valid_dists = [d for d in compared_districts if "error" not in d]
    hottest = sorted(valid_dists, key=lambda x: x["temperature_2m"], reverse=True)
    wettest = sorted(valid_dists, key=lambda x: x["precipitation_mm"], reverse=True)
    windiest = sorted(valid_dists, key=lambda x: x["wind_speed_10m"], reverse=True)

    return {
        "count": len(compared_districts),
        "districts": compared_districts,
        "rankings": {
            "hottest_district": hottest[0]["name"] if hottest else None,
            "wettest_district": wettest[0]["name"] if wettest else None,
            "windiest_district": windiest[0]["name"] if windiest else None
        }
    }


@app.get("/api/map/weather")
def get_map_weather_layers(
    variable: str = Query(default="temperature", regex="^(temperature|rainfall|humidity|wind)$")
):
    """
    Phase 2 API: District choropleth layer values for all 38 Tamil Nadu districts.
    Returns value, color thresholds, and bounds for Leaflet rendering.
    Results are cached for 15 minutes.
    """
    cache_key = f"map_layer_{variable}"
    cached_map = get_cached_item(cache_key)
    if cached_map:
        return cached_map

    variable_units = {
        "temperature": "°C",
        "rainfall": "mm",
        "humidity": "%",
        "wind": "km/h"
    }

    results = {}
    values_list = []

    def fetch_single_district_var(d_id, d_info):
        try:
            live = fetch_live_weather(d_id)
            if variable == "temperature":
                val = live.get("temperature_2m", 30.0)
            elif variable == "rainfall":
                val = live.get("precipitation_mm", 0.0)
            elif variable == "humidity":
                val = live.get("relative_humidity_2m", 65.0)
            else: # wind
                val = live.get("wind_speed_10m", 12.0)
        except Exception:
            # Fallback estimation based on elevation and zone
            if variable == "temperature":
                val = round(34.0 - (d_info["elevation_m"] / 150.0), 1)
            elif variable == "rainfall":
                val = 0.0
            elif variable == "humidity":
                val = 80.0 if d_info["is_coastal"] else 60.0
            else:
                val = 14.0 if d_info["is_coastal"] else 9.0

        return d_id, {
            "name": d_info["name"],
            "tamil_name": d_info.get("tamil_name", ""),
            "lat": d_info["lat"],
            "lon": d_info["lon"],
            "elevation_m": d_info["elevation_m"],
            "is_coastal": d_info["is_coastal"],
            "value": val,
            "unit": variable_units[variable]
        }, val

    # Parallel retrieval across districts for sub-second response
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(fetch_single_district_var, d_id, d_info)
            for d_id, d_info in TAMIL_NADU_DISTRICTS.items()
        ]
        for f in as_completed(futures):
            d_id, dist_dict, val = f.result()
            results[d_id] = dist_dict
            values_list.append(val)

    payload = {
        "variable": variable,
        "unit": variable_units[variable],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "geojson_url": "/static/tamil_nadu_districts.geojson",
        "min_value": min(values_list) if values_list else 0.0,
        "max_value": max(values_list) if values_list else 100.0,
        "districts_data": results
    }

    set_cached_item(cache_key, payload, ttl_seconds=900)
    return payload


@app.get("/api/weather/forecast/{district_id}")
def get_weather_forecast(district_id: str, days: int = Query(default=14, ge=7, le=16)):
    """Fetches 7-14 day NWP daily & hourly forecast from Open-Meteo."""
    try:
        return fetch_forecast(district_id, forecast_days=days)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/weather/predict/{district_id}")
def get_ml_prediction(district_id: str):
    """Runs inference with the self-trained Random Forest + Gradient Boosting model."""
    try:
        live_data = fetch_live_weather(district_id)
        return predictor.predict(district_id, live_data=live_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/weather/compare/{district_id}")
def compare_predictions(district_id: str):
    """
    Side-by-side Dual-Engine comparison:
    Contrasts Open-Meteo NWP forecast with the Self-Trained ML model prediction,
    with provenance attribution and historical benchmark evaluation.
    """
    try:
        dist_key = district_id.lower()
        dist_info = TAMIL_NADU_DISTRICTS.get(dist_key, TAMIL_NADU_DISTRICTS["chennai"])
        
        live_data = fetch_live_weather(dist_key)
        forecast_data = fetch_forecast(dist_key, forecast_days=7)
        ml_prediction = predictor.predict(dist_key, live_data=live_data)
        
        # 24h Comparison Metrics
        daily_next = forecast_data.get("daily", [{}])[0]
        api_rain_mm = daily_next.get("precipitation_sum_mm", 0.0)
        api_rain_prob = daily_next.get("rain_probability", 10)
        api_temp_max = daily_next.get("temp_max", 32.0)

        ml_pred = ml_prediction["predictions"]
        ml_rain_mm = ml_pred["predicted_rain_depth_mm"]
        ml_rain_prob = ml_pred["rain_probability_pct"]
        ml_temp_anomaly = ml_pred["temperature_anomaly_celsius"]

        backtest_eval = run_historical_backtest(dist_key, days=30)

        return {
            "district_id": dist_key,
            "district_name": dist_info["name"],
            "tamil_name": dist_info.get("tamil_name", ""),
            "comparison_window": "Upcoming 24-48 Hours",
            "engines": {
                "weather_api": {
                    "provider": "Open-Meteo Global NWP Model (ECMWF/GFS Physics Ensemble)",
                    "provenance_tag": "NWP Synoptic API",
                    "rain_probability_pct": api_rain_prob,
                    "rainfall_depth_mm": api_rain_mm,
                    "temperature_max_celsius": api_temp_max,
                    "historical_accuracy_pct": backtest_eval["rain_occurrence_accuracy"]["weather_api"],
                    "temp_mae_celsius": backtest_eval["temperature_mae_celsius"]["weather_api"]
                },
                "self_trained_model": {
                    "provider": "Tamil Nadu Climatological ML Ensemble (RF + GBM)",
                    "provenance_tag": "TN ML Model",
                    "rain_probability_pct": ml_rain_prob,
                    "rainfall_depth_mm": ml_rain_mm,
                    "temperature_anomaly_celsius": ml_temp_anomaly,
                    "historical_accuracy_pct": backtest_eval["rain_occurrence_accuracy"]["self_trained_model"],
                    "temp_mae_celsius": backtest_eval["temperature_mae_celsius"]["self_trained_model"],
                    "key_driving_features": ml_prediction["key_driving_features"]
                }
            },
            "consensus_analysis": {
                "rain_consensus": abs(ml_rain_mm - api_rain_mm) < 6.0,
                "delta_rain_mm": round(abs(ml_rain_mm - api_rain_mm), 1),
                "summary": (
                    f"Strong agreement on rain trends ({round(ml_rain_mm, 1)} mm ML vs. {round(api_rain_mm, 1)} mm API)."
                    if abs(ml_rain_mm - api_rain_mm) < 6.0 else
                    f"Models diverge by {round(abs(ml_rain_mm - api_rain_mm), 1)} mm. ML model accounts for micro-topography; API models synoptic storm bands."
                )
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/climate/historical/{district_id}")
def get_historical_climate(district_id: str):
    """Historical rainfall normal, seasonal trends, and monsoon departure analysis."""
    try:
        return get_district_climate_analytics(district_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# Phase 3: Climate Analytics REST API Endpoints
# ==============================================================================

@app.get("/api/climate/trends")
def get_climate_trends(
    district: str = Query(default="chennai"),
    start_year: int = Query(default=2015, ge=2010, le=2024),
    end_year: int = Query(default=2024, ge=2010, le=2024),
    season: str = Query(default="all"),
    variable: str = Query(default="all")
):
    """Historical temperature and rainfall trends with decadal warming rate and rainy days."""
    try:
        return get_historical_trends(district_id=district, start_year=start_year, end_year=end_year, season=season, variable=variable)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/climate/seasonal-rainfall")
def get_monsoon_seasonal_rainfall(
    district: Optional[str] = Query(default=None),
    year: int = Query(default=2024, ge=2010, le=2024),
    season: str = Query(default="all")
):
    """Monsoon and seasonal rainfall analysis with 38-district rankings and departure categories."""
    try:
        return get_seasonal_rainfall(district_id=district, year=year, season=season)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/climate/anomalies")
def get_climatological_anomalies(
    district: str = Query(default="chennai"),
    start_year: int = Query(default=2015, ge=2010, le=2024),
    end_year: int = Query(default=2024, ge=2010, le=2024),
    baseline: str = Query(default="1991-2020")
):
    """Temperature and rainfall anomalies matrix heatmap with dry spells and extreme event detection."""
    try:
        return get_climate_anomalies(district_id=district, start_year=start_year, end_year=end_year, baseline=baseline)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/climate/district-comparison")
def compare_selected_districts(
    districts: str = Query(default="chennai,coimbatore,madurai,nilgiris"),
    period: str = Query(default="10_year")
):
    """Side-by-side climate normal and multi-year comparison for selected districts."""
    try:
        d_list = [d.strip() for d in districts.split(",") if d.strip()]
        return compare_district_climates(districts_list=d_list, period=period)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/climate/summary")
def get_climate_indicators_summary(
    district: str = Query(default="all"),
    year: int = Query(default=2024, ge=2010, le=2024)
):
    """Statewide climate indicators, extreme district highlights, and key scientific findings."""
    try:
        return get_climate_summary(district_id=district, year=year)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ReportGenerationRequest(BaseModel):
    district: str = "chennai"
    start_year: int = 2015
    end_year: int = 2024
    season: str = "all"
    variable: str = "all"
    format: str = "both"


@app.post("/api/climate/reports")
def create_climate_report(req: ReportGenerationRequest):
    """Generates downloadable climate report dossier in PDF and CSV formats."""
    try:
        return generate_climate_report(
            district_id=req.district,
            start_year=req.start_year,
            end_year=req.end_year,
            season=req.season,
            variable=req.variable,
            format_type=req.format
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/climate/reports/{report_id}")
def get_report_metadata(report_id: str):
    """Retrieves metadata and generation status for a generated report."""
    report = get_climate_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Climate report not found")
    return report


@app.get("/api/climate/reports/{report_id}/download")
def download_climate_report(
    report_id: str,
    format: str = Query(default="pdf", regex="^(pdf|csv)$")
):
    """Downloads generated climate report file in PDF or CSV format."""
    report = get_climate_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Climate report not found")
    
    file_path = report.get("pdf_path") if format == "pdf" else report.get("csv_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Report file for format '{format}' not found on disk")
    
    media_type = "application/pdf" if format == "pdf" else "text/csv"
    ext = "pdf" if format == "pdf" else "csv"
    download_filename = f"{report_id}_{report['district_id']}.{ext}"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=download_filename,
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'}
    )


@app.get("/api/risks")
def get_risks():
    """Returns statewide risk monitoring matrix for all 38 districts."""
    return get_statewide_risk_matrix()


@app.get("/api/impacts/{district_id}")
def get_district_impacts(district_id: str):
    """Evaluates agriculture, water resources, transport, and health impacts."""
    try:
        dist_key = district_id.lower()
        live_data = fetch_live_weather(dist_key)
        forecast_data = fetch_forecast(dist_key, forecast_days=7)
        ml_prediction = predictor.predict(dist_key, live_data=live_data)
        return evaluate_sector_impacts(dist_key, live_data, forecast_data, ml_prediction)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/backtest/{district_id}")
def get_backtest_evaluation(district_id: str, days: int = 30):
    """Returns backtested accuracy benchmark between API and Self-Trained model."""
    try:
        return run_historical_backtest(district_id, days=days)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class InsightRequest(BaseModel):
    district_id: str


@app.post("/api/insights/generate")
def generate_insights(req: InsightRequest):
    """Generates AI natural language briefing explaining forecast and risk dynamics."""
    dist_key = req.district_id.lower()
    dist_info = TAMIL_NADU_DISTRICTS.get(dist_key, TAMIL_NADU_DISTRICTS["chennai"])
    
    live_data = fetch_live_weather(dist_key)
    forecast_data = fetch_forecast(dist_key, forecast_days=7)
    ml_prediction = predictor.predict(dist_key, live_data=live_data)
    sector_impacts = evaluate_sector_impacts(dist_key, live_data, forecast_data, ml_prediction)

    return generate_climate_ai_insight(
        district_name=dist_info["name"],
        district_info=dist_info,
        live_weather=live_data,
        forecast_data=forecast_data,
        ml_prediction=ml_prediction,
        sector_impacts=sector_impacts
    )


# ==============================================================================
# Phase 4 — AI Models & Leakage-Free Forecast Evaluation Endpoints
# ==============================================================================
@app.get("/api/ml/experiments")
def get_ml_experiments_endpoint():
    """Returns Phase 4 experiment manifest, model leaderboard, and split metadata."""
    try:
        return get_ml_experiments_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/models")
def get_ml_models_endpoint():
    """Returns registered forecasting models and validation/test scores."""
    try:
        return get_ml_models_registry()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/forecast")
def get_ml_forecast_endpoint(
    district: str = Query("chennai", description="District ID"),
    horizon: int = Query(24, description="Forecast horizon in hours (24 or 72)")
):
    """Produces live inference using the champion LightGBM model with 80% & 95% confidence intervals."""
    try:
        return get_live_ml_forecast(district_id=district, horizon_hours=horizon)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/ml/backtest-results")
def get_ml_backtest_results_endpoint(
    district: Optional[str] = Query("chennai", description="District ID filter"),
    limit: int = Query(40, description="Number of historical test evaluation points")
):
    """Returns time-series actuals vs model predictions and prediction intervals for test split."""
    try:
        return get_backtest_eval_series(district_id=district, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/ml/timesfm-benchmark")
def get_timesfm_benchmark_endpoint():
    """Returns in-depth comparative benchmark between Hugging Face TimesFM and localized LightGBM."""
    try:
        return get_timesfm_operational_benchmark()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BacktestRunRequest(BaseModel):
    horizon_hours: int = 24


@app.post("/api/ml/run-backtest")
def trigger_backtest_endpoint(req: BacktestRunRequest):
    """Executes a full chronological rolling-origin backtest and updates registry."""
    try:
        return execute_chronological_backtest(horizon_hours=req.horizon_hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# Phase 5 — Risk Intelligence REST Endpoints
# ==============================================================================
@app.get("/api/risk/overview")
def get_risk_overview_endpoint():
    """Returns overall risk summary, severity distribution, and active alerts across Tamil Nadu."""
    try:
        return evaluate_statewide_risk_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/districts")
def get_risk_districts_endpoint():
    """Returns district-level risk assessments for all 38 Tamil Nadu districts."""
    try:
        return get_all_district_risk_summaries()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/alerts")
def get_risk_alerts_endpoint(
    district: Optional[str] = Query(None, description="Filter by district ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (Low, Moderate, High, Severe)"),
    hazard: Optional[str] = Query(None, description="Filter by hazard type (rainfall, heat, wind, dry_spell)"),
    status: Optional[str] = Query(None, description="Filter by status (Active, Updated, Resolved)"),
    limit: int = Query(50, description="Max records to return")
):
    """Returns searchable alert history from SQLite with audit and lifecycle information."""
    try:
        return get_alerts_list(
            district_id=district,
            severity=severity,
            hazard_type=hazard,
            status=status,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/alerts/export")
def export_risk_alerts_endpoint(
    district: Optional[str] = Query(None, description="Filter by district ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    hazard: Optional[str] = Query(None, description="Filter by hazard type")
):
    """Exports alert history with full audit provenance to CSV."""
    try:
        csv_data = export_alerts_to_csv_string(district_id=district, severity=severity, hazard_type=hazard)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="tamil_nadu_risk_alerts.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/alerts/{alert_id}")
def get_risk_alert_details_endpoint(alert_id: str):
    """Returns detailed alert information including measured trigger values, thresholds, and audit log."""
    alert = get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return alert


@app.patch("/api/risk/alerts/{alert_id}")
def patch_risk_alert_endpoint(alert_id: str):
    """Acknowledges an alert by an operator and records the acknowledgment in the audit log."""
    updated = acknowledge_alert(alert_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return {
        "status": "SUCCESS",
        "message": f"Alert {alert_id} acknowledged successfully.",
        "alert": updated
    }


@app.get("/api/risk/thresholds")
def get_risk_thresholds_endpoint():
    """Returns active transparent application thresholds and official IMD criteria."""
    try:
        return get_threshold_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/warnings/official")
def get_official_warnings_endpoint(district: Optional[str] = Query(None, description="District ID")):
    """Returns official warnings from IMD / RMC Chennai with direct links and disclaimers."""
    try:
        return get_official_imd_warnings(district_id=district)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/summaries/{district}")
def get_district_bilingual_summary_endpoint(district: str):
    """Returns deterministic bilingual English and Tamil risk summary for a district."""
    try:
        return get_single_district_bilingual_summary(district_id=district)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# OPERATIONAL INTELLIGENCE LAYER: MODULES 1, 2, 3
# ============================================================================

class DataSourceUpdatePayload(BaseModel):
    is_enabled: bool
    performed_by: Optional[str] = "operator"


class OperationalSettingUpdatePayload(BaseModel):
    setting_key: str
    setting_value: str
    performed_by: Optional[str] = "operator"


# ----------------------------------------------------------------------------
# Module 1: Computed Meteorological Guidance & Atmospheric Context
# ----------------------------------------------------------------------------
@app.get("/api/guidance/{district_id}")
def get_computed_guidance_endpoint(district_id: str):
    """
    Module 1: Computed Meteorological Guidance & Atmospheric Context
    Translates forecast variables into computed meteorological indicators, atmospheric context,
    multi-horizon forecast evolution (6h, 24h, 48h, 72h), and explainable triggers with
    traceability metadata.
    """
    try:
        return generate_meteorological_guidance(district_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# Module 2: Multi-Sector Operational Impact Matrix
# ----------------------------------------------------------------------------
@app.get("/api/sectors/matrix")
def get_sector_matrix_endpoint(
    district_id: Optional[str] = Query(None, description="Optional district ID"),
    sector: Optional[str] = Query(None, description="Optional sector key filter"),
    horizon: int = Query(24, description="Forecast horizon in hours: 6, 24, 48, 72")
):
    """
    Module 2: Multi-Sector Operational Impact Matrix
    Translates meteorological conditions into 7 sector-specific implications:
    Agriculture, Transport & Logistics, Urban Infrastructure, Water Resources,
    Coastal Operations, Public Health, and Renewable Energy.
    Decomposes into Hazard Likelihood, District Exposure, and Vulnerability.
    """
    try:
        if district_id:
            return evaluate_district_sector_matrix(district_id, horizon_hours=horizon)
        return get_all_districts_sector_matrix(sector_filter=sector, horizon_hours=horizon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sectors/matrix/export")
def export_sector_matrix_csv_endpoint(
    sector: Optional[str] = Query(None, description="Optional sector filter"),
    horizon: int = Query(24, description="Forecast horizon in hours: 6, 24, 48, 72")
):
    """
    Exports multi-sector impact matrix across all 38 districts as standard RFC 4180 CSV
    with assessment timestamps and meteorological data provenance.
    """
    try:
        csv_data = export_sector_matrix_to_csv_string(sector_filter=sector, horizon_hours=horizon)
        filename = f"tn_sector_impact_matrix_{horizon}h.csv" if not sector else f"tn_{sector}_impact_matrix_{horizon}h.csv"
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# Module 3: Settings & Meteorological Data Sources
# ----------------------------------------------------------------------------
@app.get("/api/settings/sources")
def get_data_sources_endpoint():
    """Module 3: Meteorological Data Sources Registry (Open-Meteo, IMD, NASA POWER, Copernicus, Hugging Face)."""
    try:
        return get_data_sources_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/settings/sources/{source_id}")
def update_data_source_endpoint(source_id: str, payload: DataSourceUpdatePayload):
    """Toggles enabled status of a meteorological data source and records entry in audit log."""
    try:
        return update_data_source_status(
            source_id=source_id,
            is_enabled=payload.is_enabled,
            performed_by=payload.performed_by or "operator"
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/config")
def get_operational_config_endpoint():
    """Returns persistent operational configuration and risk thresholds from SQLite."""
    try:
        return get_operational_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/settings/config")
def update_operational_config_endpoint(payload: OperationalSettingUpdatePayload):
    """Updates an operational threshold or setting and appends to persistent audit log."""
    try:
        return update_operational_setting(
            setting_key=payload.setting_key,
            setting_value=payload.setting_value,
            performed_by=payload.performed_by or "operator"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/audit")
def get_operational_audit_endpoint(limit: int = Query(50, description="Max audit entries to retrieve")):
    """Retrieves audit trail of changed thresholds, data sources, and system operations."""
    try:
        return get_operational_audit_log(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/settings/health")
def get_sources_health_endpoint():
    """Observability health check across registered meteorological sources."""
    try:
        return check_data_sources_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve Frontend Static Files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/style.css")
    def serve_css():
        return FileResponse(os.path.join(frontend_dir, "style.css"), media_type="text/css")

    @app.get("/app.js")
    def serve_js():
        return FileResponse(os.path.join(frontend_dir, "app.js"), media_type="application/javascript")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
