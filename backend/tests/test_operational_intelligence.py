"""
Automated Test Suite for Operational Intelligence Layer
Modules Tested:
1. Computed Meteorological Guidance & Atmospheric Context
2. Multi-Sector Operational Impact Matrix
3. Settings & Meteorological Data Sources Registry
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.guidance.indicators import (
    compute_apparent_temperature,
    compute_rainfall_accumulations,
    compute_rainfall_anomaly,
    compute_wind_exposure,
    compute_dew_point_spread,
    compute_pressure_tendency,
    compute_dry_spell_metrics
)
from backend.services.guidance.guidance_engine import generate_meteorological_guidance
from backend.services.impact.sector_matrix import (
    evaluate_district_sector_matrix,
    get_all_districts_sector_matrix,
    SECTOR_DRIVER_WEIGHTS
)
from backend.services.impact.sector_export import export_sector_matrix_to_csv_string
from backend.services.settings.source_registry import (
    get_data_sources_list,
    update_data_source_status,
    get_operational_settings,
    update_operational_setting,
    get_operational_audit_log,
    check_data_sources_health
)

client = TestClient(app)


# ============================================================================
# MODULE 1: COMPUTED METEOROLOGICAL GUIDANCE TESTS
# ============================================================================

def test_meteorological_indicator_formulas():
    """Validates mathematical correctness of core meteorological indicator functions."""
    # 1. Apparent Temperature / Heat Index
    thermal_hot = compute_apparent_temperature(38.0, 75.0, 10.0)
    assert thermal_hot["heat_index_c"] > 40.0
    assert thermal_hot["apparent_temperature_c"] > 38.0
    assert thermal_hot["category"] in ["High", "Severe"]

    # 2. Dew Point Spread
    dew = compute_dew_point_spread(32.0, 30.0)
    assert dew["dew_point_spread_c"] == 2.0
    assert "moist" in dew["moisture_context"].lower() or "humidity" in dew["moisture_context"].lower()

    # 3. Pressure Tendency
    p_drop = compute_pressure_tendency(1005.0, 1010.0)
    assert p_drop["delta_3h_hpa"] == -5.0
    assert p_drop["tendency"] == "Rapidly Falling"
    assert "does not predict cyclonic storms" in p_drop["meteorological_disclaimer"].lower()

    # 4. Wind Exposure
    wind_gale = compute_wind_exposure(45.0, 68.0, is_coastal=True)
    assert wind_gale["level"] in ["Moderate", "High", "Severe"]
    assert "gust" in wind_gale["guidance"].lower() or "breeze" in wind_gale["guidance"].lower()

    # 5. Rainfall Anomaly
    ano_wet = compute_rainfall_anomaly(rain_24h=25.0, annual_normal_mm=1200.0, nem_normal_mm=800.0, month=10)
    assert "departure_pct" in ano_wet
    assert "departure_category" in ano_wet


def test_guidance_engine_structure():
    """Validates that guidance engine produces 4 atmospheric sections, multi-horizon evolution, and triggers."""
    res = generate_meteorological_guidance("chennai")
    assert res["district_id"] == "chennai"
    assert "traceability" in res
    assert "last_updated_utc" in res["traceability"]

    # 4 Main atmospheric context sections
    assert "thermal_conditions" in res
    assert "precipitation" in res
    assert "atmospheric_flow" in res
    assert "atmospheric_state" in res

    # Check required fields within sections
    assert "heat_index_c" in res["thermal_conditions"]
    assert "accumulation_6h_mm" in res["precipitation"]
    assert "accumulation_24h_mm" in res["precipitation"]
    assert "accumulation_48h_mm" in res["precipitation"]
    assert "accumulation_72h_mm" in res["precipitation"]

    assert "wind_speed_kmh" in res["atmospheric_flow"]
    assert "pressure_tendency" in res["atmospheric_state"]
    assert "instability_proxy" in res["atmospheric_state"]

    # Multi-horizon forecast evolution (6h, 24h, 48h, 72h)
    evo = res["forecast_evolution"]
    for horizon in ["6h", "24h", "48h", "72h"]:
        assert horizon in evo
        assert "expected_temperature_c" in evo[horizon]
        assert "expected_rain_accumulation_mm" in evo[horizon]

    # Computed guidance triggers & traceability
    assert "active_triggers" in res
    assert "Open-Meteo" in res["traceability"]["primary_source"]


# ============================================================================
# MODULE 2: MULTI-SECTOR OPERATIONAL IMPACT MATRIX TESTS
# ============================================================================

def test_sector_matrix_seven_sectors():
    """Validates that all 7 required sectors are evaluated with H, E, V and composite scores."""
    res = evaluate_district_sector_matrix("chennai", horizon_hours=24)
    sectors = res["sectors"]
    expected_sectors = [
        "agriculture",
        "transport_and_logistics",
        "urban_infrastructure",
        "water_resources",
        "coastal_operations",
        "public_health",
        "renewable_energy"
    ]
    for s_key in expected_sectors:
        assert s_key in sectors, f"Missing sector {s_key}"
        sec = sectors[s_key]
        assert "hazard_likelihood" in sec
        assert "exposure_score" in sec
        assert "vulnerability_score" in sec
        assert "composite_score" in sec
        assert "severity" in sec
        assert "meteorological_drivers" in sec
        assert "recommended_guidance" in sec
        assert 0.0 <= sec["composite_score"] <= 100.0


def test_sector_matrix_statewide_and_export():
    """Validates 38-district statewide matrix computation and CSV export serialization."""
    # Statewide
    all_districts = get_all_districts_sector_matrix(sector_filter="urban_infrastructure", horizon_hours=24)
    assert len(all_districts) == 38
    for d in all_districts:
        assert "urban_infrastructure" in d["sectors"]
        assert "highlighted_sector" in d

    # CSV Export
    csv_str = export_sector_matrix_to_csv_string(sector_filter="agriculture", horizon_hours=48)
    assert "District_ID,District_Name,Tamil_Name" in csv_str
    assert "agriculture" in csv_str.lower()
    assert "Chennai" in csv_str


# ============================================================================
# MODULE 3: SETTINGS & METEOROLOGICAL DATA SOURCES TESTS
# ============================================================================

def test_data_sources_registry_and_toggle():
    """Validates retrieving registry, toggling data source, and audit trail persistence."""
    sources = get_data_sources_list()
    assert len(sources) >= 5
    source_ids = [s["source_id"] for s in sources]
    assert "open_meteo" in source_ids
    assert "imd_rmc" in source_ids
    assert "nasa_power" in source_ids
    assert "copernicus_cds" in source_ids
    assert "huggingface" in source_ids

    # Toggle open_meteo
    res = update_data_source_status("open_meteo", is_enabled=False, performed_by="test_suite")
    assert res["status"] == "SUCCESS"
    assert res["is_enabled"] is False

    # Check updated
    sources_after = get_data_sources_list()
    om = next(s for s in sources_after if s["source_id"] == "open_meteo")
    assert om["is_enabled"] is False

    # Re-enable open_meteo
    update_data_source_status("open_meteo", is_enabled=True, performed_by="test_suite")


def test_operational_settings_and_audit_log():
    """Validates reading/updating operational settings and inspecting audit log entries."""
    settings = get_operational_settings()
    assert "default_forecast_horizon_hours" in settings
    assert "rain_accumulation_window_hours" in settings

    # Update threshold
    res = update_operational_setting("heavy_rainfall_threshold_mm", "70.0", performed_by="admin_test")
    assert res["status"] == "SUCCESS"
    assert res["new_value"] == "70.0"

    # Verify audit log recorded the update
    audit = get_operational_audit_log(limit=10)
    assert len(audit) > 0
    recent_entry = audit[0]
    assert recent_entry["target"] == "operational_settings:heavy_rainfall_threshold_mm"
    assert recent_entry["performed_by"] == "admin_test"


def test_sources_health_observability():
    """Validates observability health check endpoint."""
    health = check_data_sources_health()
    assert health["status"] == "OPERATIONAL"
    assert health["total_sources_registered"] >= 5
    assert health["active_sources_count"] >= 1


# ============================================================================
# FASTAPI ENDPOINT INTEGRATION TESTS
# ============================================================================

def test_fastapi_guidance_endpoint():
    """Tests GET /api/guidance/{district_id}"""
    response = client.get("/api/guidance/chennai")
    assert response.status_code == 200
    data = response.json()
    assert data["district_id"] == "chennai"
    assert "thermal_conditions" in data
    assert "precipitation" in data
    assert "atmospheric_flow" in data
    assert "atmospheric_state" in data
    assert "forecast_evolution" in data
    assert "active_triggers" in data


def test_fastapi_sector_matrix_endpoints():
    """Tests GET /api/sectors/matrix and GET /api/sectors/matrix/export"""
    # Single district matrix
    r1 = client.get("/api/sectors/matrix?district_id=chennai&horizon=24")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["district_id"] == "chennai"
    assert len(d1["sectors"]) == 7

    # Statewide matrix
    r2 = client.get("/api/sectors/matrix?sector=urban_infrastructure&horizon=48")
    assert r2.status_code == 200
    d2 = r2.json()
    assert isinstance(d2, list)
    assert len(d2) == 38

    # CSV Export
    r3 = client.get("/api/sectors/matrix/export?horizon=24")
    assert r3.status_code == 200
    assert "text/csv" in r3.headers["content-type"]
    assert "attachment; filename=" in r3.headers["content-disposition"]
    assert "District_ID" in r3.text


def test_fastapi_settings_and_sources_endpoints():
    """Tests GET/PATCH /api/settings/sources, GET/PATCH /api/settings/config, audit, and health."""
    # 1. Sources GET
    r_src = client.get("/api/settings/sources")
    assert r_src.status_code == 200
    assert len(r_src.json()) >= 5

    # 2. Source PATCH
    r_patch = client.patch(
        "/api/settings/sources/nasa_power",
        json={"is_enabled": True, "performed_by": "qa_agent"}
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["status"] == "SUCCESS"

    # 3. Config GET
    r_cfg = client.get("/api/settings/config")
    assert r_cfg.status_code == 200
    assert "default_forecast_horizon_hours" in r_cfg.json()

    # 4. Config PATCH
    r_cfg_patch = client.patch(
        "/api/settings/config",
        json={"setting_key": "cache_ttl_forecast_seconds", "setting_value": "3600", "performed_by": "qa_agent"}
    )
    assert r_cfg_patch.status_code == 200
    assert r_cfg_patch.json()["new_value"] == "3600"

    # 5. Audit GET
    r_aud = client.get("/api/settings/audit?limit=20")
    assert r_aud.status_code == 200
    assert isinstance(r_aud.json(), list)

    # 6. Health GET
    r_hlth = client.get("/api/settings/health")
    assert r_hlth.status_code == 200
    assert r_hlth.json()["status"] == "OPERATIONAL"
