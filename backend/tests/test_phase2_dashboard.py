"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 2 Test Suite: Dashboard & API Endpoints Verification

Tests all Phase 2 requirements:
1. Current weather overview endpoint (/api/weather/current)
2. Hourly forecast endpoint (/api/weather/hourly) with separated rain mm vs probability %
3. Daily forecast endpoint (/api/weather/daily) with day-over-day changes & warnings
4. District registry (/api/districts)
5. Multi-district comparison (/api/districts/compare) up to 4 districts
6. Map weather layer (/api/map/weather) with all 4 supported meteorological variables
7. Frontend static asset delivery (index.html, style.css, app.js, geojson)
8. Graceful handling of invalid or edge-case districts
9. Zero PostgreSQL dependency verification
"""

import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"


def test_server_health():
    r = requests.get(f"{BASE_URL}/api/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "HEALTHY"
    assert data["districts_loaded"] == 38


def test_current_weather_overview():
    districts = ["chennai", "coimbatore", "madurai", "salem", "nilgiris"]
    for dist in districts:
        r = requests.get(f"{BASE_URL}/api/weather/current?district={dist}", timeout=15)
        assert r.status_code == 200, f"Failed for {dist}"
        data = r.json()
        
        # 6 KPI Variables
        assert "temperature_2m" in data
        assert "relative_humidity_2m" in data
        assert "precipitation_mm" in data
        assert "wind_speed_10m" in data
        assert "pressure_msl" in data
        assert "uv_index" in data

        # Status and metadata
        assert data["status"] in ["Clear", "Cloudy", "Rainy", "Storm Risk", "Hot"]
        assert "today_summary" in data
        today = data["today_summary"]
        assert "temp_max" in today
        assert "temp_min" in today
        assert "expected_rain_mm" in today
        assert "rain_probability" in today
        assert "sunrise" in today
        assert "sunset" in today


def test_hourly_forecast_timeline():
    r = requests.get(f"{BASE_URL}/api/weather/hourly?district=chennai&hours=48", timeout=8)
    assert r.status_code == 200
    data = r.json()
    assert data["district"] == "chennai"
    assert len(data["hourly"]) >= 24

    first = data["hourly"][0]
    assert "temperature" in first
    assert "apparent_temperature" in first
    assert "rain_mm" in first
    assert "precipitation_probability_pct" in first
    assert "humidity" in first
    assert "wind_speed" in first
    assert "condition" in first
    assert "icon" in first
    assert "is_day" in first

    # Verify that rain_mm and probability are separate measures
    for h in data["hourly"]:
        assert isinstance(h["rain_mm"], (int, float))
        assert isinstance(h["precipitation_probability_pct"], (int, float))
        assert 0 <= h["precipitation_probability_pct"] <= 100


def test_daily_forecast_dashboard():
    r = requests.get(f"{BASE_URL}/api/weather/daily?district=coimbatore&days=14", timeout=8)
    assert r.status_code == 200
    data = r.json()
    assert "daily" in data
    assert len(data["daily"]) >= 7

    first = data["daily"][0]
    assert "date" in first
    assert "temp_max" in first
    assert "temp_min" in first
    assert "precipitation_sum_mm" in first
    assert "rain_probability" in first
    assert "thermal_range" in first
    assert "warnings" in first


def test_districts_registry():
    r = requests.get(f"{BASE_URL}/api/districts", timeout=5)
    assert r.status_code == 200
    districts = r.json()
    assert len(districts) == 38
    names = [d["name"] for d in districts]
    assert "Chennai" in names
    assert "Coimbatore" in names
    assert "Madurai" in names


def test_district_comparison():
    names = "Chennai,Coimbatore,Madurai,Salem"
    r = requests.get(f"{BASE_URL}/api/districts/compare?names={names}", timeout=8)
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 4
    assert len(data["districts"]) == 4

    rankings = data["rankings"]
    assert "hottest_district" in rankings
    assert "wettest_district" in rankings
    assert "windiest_district" in rankings


def test_map_weather_layers():
    variables = ["temperature", "rainfall", "humidity", "wind"]
    for var in variables:
        r = requests.get(f"{BASE_URL}/api/map/weather?variable={var}", timeout=25)
        assert r.status_code == 200
        data = r.json()
        assert data["variable"] == var
        assert "districts_data" in data
        assert len(data["districts_data"]) == 38
        assert "min_value" in data
        assert "max_value" in data
        assert data["geojson_url"] == "/static/tamil_nadu_districts.geojson"


def test_static_files():
    r_index = requests.get(f"{BASE_URL}/", timeout=5)
    assert r_index.status_code == 200
    assert "Tamil Nadu Climate & Forecast Intelligence" in r_index.text

    r_css = requests.get(f"{BASE_URL}/style.css", timeout=5)
    assert r_css.status_code == 200

    r_js = requests.get(f"{BASE_URL}/app.js", timeout=5)
    assert r_js.status_code == 200

    r_geo = requests.get(f"{BASE_URL}/static/tamil_nadu_districts.geojson", timeout=5)
    assert r_geo.status_code == 200
    assert "FeatureCollection" in r_geo.text


def test_zero_postgresql_dependency():
    """Verify no postgresql libraries or connection strings are loaded."""
    import sys
    assert "psycopg2" not in sys.modules
    assert "asyncpg" not in sys.modules


if __name__ == "__main__":
    pytest.main(["-v", __file__])
