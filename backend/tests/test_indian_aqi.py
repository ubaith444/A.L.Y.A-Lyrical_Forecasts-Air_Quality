import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_cache, get_provider
from app.main import app
from app.services.aqi import (
    calculate_sub_index,
    compute_indian_aqi,
    get_cpcb_category_and_guidance,
)


def test_calculate_sub_index_breakpoints():
    # PM2.5 breakpoints: 0-30 -> 0-50, 30.1-60 -> 51-100, 60.1-90 -> 101-200
    assert calculate_sub_index("pm2_5", 15.0) == pytest.approx(25.0, 0.5)
    assert calculate_sub_index("pm2_5", 45.0) == pytest.approx(75.5, 1.0)
    assert calculate_sub_index("pm2_5", 75.0) == pytest.approx(150.5, 1.0)

    # PM10 breakpoints: 0-50 -> 0-50, 51-100 -> 51-100, 101-250 -> 101-200
    assert calculate_sub_index("pm10", 25.0) == pytest.approx(25.0, 0.5)
    assert calculate_sub_index("pm10", 75.0) == pytest.approx(75.0, 1.0)

    # NO2 breakpoints: 0-40 -> 0-50, 41-80 -> 51-100
    assert calculate_sub_index("nitrogen_dioxide", 20.0) == pytest.approx(25.0, 0.5)

    # Negative concentration returns None
    assert calculate_sub_index("pm2_5", -5.0) is None


def test_get_cpcb_category_and_guidance():
    cat, msg = get_cpcb_category_and_guidance(35)
    assert cat == "Good"
    assert "Minimal" in msg

    cat, msg = get_cpcb_category_and_guidance(75)
    assert cat == "Satisfactory"

    cat, msg = get_cpcb_category_and_guidance(150)
    assert cat == "Moderate"

    cat, msg = get_cpcb_category_and_guidance(250)
    assert cat == "Poor"

    cat, msg = get_cpcb_category_and_guidance(350)
    assert cat == "Very Poor"

    cat, msg = get_cpcb_category_and_guidance(450)
    assert cat == "Severe"


def test_compute_indian_aqi_requires_minimum_pollutants():
    # Only 2 pollutants (e.g., pm2_5 and pm10) -> Should fail minimum 3 pollutants rule
    hourly_insufficient = {
        "pm2_5": [25.0] * 24,
        "pm10": [50.0] * 24,
    }
    result = compute_indian_aqi(hourly_insufficient)
    assert result["status"] == "unavailable"
    assert result["value"] is None
    assert "at least 3 monitored pollutants" in result["reason"]


def test_compute_indian_aqi_requires_particulate_matter():
    # 3 pollutants (NO2, SO2, CO) but NO PM2.5 or PM10 -> Should fail CPCB particulate rule
    hourly_no_pm = {
        "nitrogen_dioxide": [30.0] * 24,
        "sulphur_dioxide": [20.0] * 24,
        "carbon_monoxide": [500.0] * 24,
    }
    result = compute_indian_aqi(hourly_no_pm)
    assert result["status"] == "unavailable"
    assert result["value"] is None
    assert "particulate matter" in result["reason"]


def test_compute_indian_aqi_requires_minimum_valid_hours():
    # Only 10 hours of PM2.5 (requires >= 16) -> should fail
    hourly_short = {
        "pm2_5": [25.0] * 10,
        "pm10": [50.0] * 24,
        "nitrogen_dioxide": [30.0] * 24,
    }
    result = compute_indian_aqi(hourly_short)
    assert result["status"] == "unavailable"


def test_compute_indian_aqi_successful_calculation():
    # Valid 24 hours of PM2.5, PM10, NO2, SO2, CO (in µg/m³), O3
    # PM2.5 = 75 µg/m³ -> sub-index ~ 150 (Moderate)
    # PM10 = 80 µg/m³ -> sub-index ~ 80 (Satisfactory)
    # NO2 = 30 µg/m³ -> sub-index ~ 37.5 (Good)
    # CO = 2500 µg/m³ -> 2.5 mg/m³ -> sub-index in 2.01-10.0 bracket ~ 107
    hourly_full = {
        "pm2_5": [75.0] * 24,
        "pm10": [80.0] * 24,
        "nitrogen_dioxide": [30.0] * 24,
        "sulphur_dioxide": [20.0] * 24,
        "carbon_monoxide": [2500.0] * 24,
        "ozone": [40.0] * 24,
    }
    result = compute_indian_aqi(hourly_full)
    assert result["status"] == "calculated"
    assert result["value"] == pytest.approx(150, abs=2)
    assert result["dominant_pollutant"] == "pm2_5"
    assert result["category"] == "Moderate"
    assert "Breathing discomfort" in result["health_guidance"]
    assert "pm2_5" in result["sub_indices"]
    assert "pm10" in result["sub_indices"]
    assert "carbon_monoxide" in result["sub_indices"]


class FullAirQualityProvider:
    async def air_quality(self, **kwargs):
        return {
            "current": {
                "time": "2026-10-24T12:00",
                "us_aqi": 155,
                "european_aqi": 65,
                "pm2_5": 72.0,
                "pm10": 110.0,
                "nitrogen_dioxide": 45.0,
                "ozone": 55.0,
                "sulphur_dioxide": 22.0,
                "carbon_monoxide": 1800.0,
            },
            "current_units": {
                "us_aqi": "",
                "european_aqi": "",
                "pm2_5": "μg/m³",
                "pm10": "μg/m³",
                "nitrogen_dioxide": "μg/m³",
                "ozone": "μg/m³",
                "sulphur_dioxide": "μg/m³",
                "carbon_monoxide": "μg/m³",
            },
            "hourly": {
                "time": [f"2026-10-24T{h:02d}:00" for h in range(24)],
                "pm2_5": [75.0] * 24,
                "pm10": [80.0] * 24,
                "nitrogen_dioxide": [30.0] * 24,
                "sulphur_dioxide": [20.0] * 24,
                "carbon_monoxide": [2500.0] * 24,
                "ozone": [40.0] * 24,
            },
        }


class DirectCache:
    async def get_or_fetch(self, namespace, params, fetch):
        from datetime import UTC, datetime

        return await fetch(), False, datetime(2026, 10, 24, tzinfo=UTC)


def test_air_quality_route_with_cpcb_and_multiple_standards():
    app.dependency_overrides[get_provider] = lambda: FullAirQualityProvider()
    app.dependency_overrides[get_cache] = lambda: DirectCache()
    try:
        response = TestClient(app).get(
            "/api/v1/air-quality", params={"location_id": "new-delhi"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()

    # Standards explicitly present
    assert body["aqi"]["standard"] == "US EPA AQI"
    assert body["aqi"]["value"] == 155
    assert body["aqi"]["european_aqi"] == 65

    # CPCB Indian AQI computed successfully
    assert body["aqi"]["indian_aqi"] is not None
    assert body["aqi"]["indian_aqi"] > 0
    assert "Available" in body["aqi"]["indian_aqi_status"]
    assert body["aqi"]["cpcb_details"]["dominant_pollutant"] == "pm2_5"
    assert "not interchangeable" in body["aqi"]["standards_disclaimer"]

    # Health guidance follows CPCB
    assert body["health_guidance"]["standard"] == "Indian CPCB NAQI"
    assert body["health_guidance"]["category"] == "Moderate"

    # Pollutants properly mapped
    assert body["pollutants"]["pm2_5"]["value"] == 72.0
    assert body["pollutants"]["pm2_5"]["unit"] == "μg/m³"
    assert body["pollutants"]["pm2_5"]["status"] == "available"
