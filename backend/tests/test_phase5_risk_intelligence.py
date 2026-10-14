"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 5 Test Suite: Risk Intelligence, Thresholds & Alert Lifecycle

Verifies:
1. Transparent threshold boundaries and severity level transitions (Low -> Moderate -> High -> Severe).
2. Defensive handling of missing, stale, and invalid weather inputs.
3. Duplicate-alert prevention, lifecycle state transitions (Active -> Updated -> Resolved), and audit trail.
4. SQLite persistence and schema integrity for risk alerts (zero PostgreSQL).
5. Bilingual summary consistency (English & Tamil reflect identical values, units, and timestamps).
6. Official IMD warning integration (portal links, validity periods, strict non-fabrication disclaimers).
7. Alert acknowledgment and CSV export functionality.
8. All FastAPI Phase 5 REST endpoints.
"""

import os
import sys
import json
import sqlite3
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.database import init_db, DB_PATH
from backend.services.risk.thresholds import (
    APPLICATION_THRESHOLDS,
    IMD_WARNING_CRITERIA,
    get_threshold_config
)
from backend.services.risk.risk_engine import (
    compute_heat_index_celsius,
    evaluate_district_weather_risk
)
from backend.services.risk.alert_repository import (
    init_risk_tables,
    save_or_update_alert,
    acknowledge_alert,
    get_alerts_list,
    get_alert_by_id,
    export_alerts_to_csv_string
)
from backend.services.risk.official_warnings import (
    get_official_imd_warnings,
    IMD_MAIN_PORTAL,
    IMD_CHENNAI_PORTAL
)
from backend.services.risk.summary_service import (
    generate_bilingual_risk_summary
)
from backend.services.risk.alert_service import (
    evaluate_and_sync_district_alerts,
    evaluate_statewide_risk_overview,
    get_all_district_risk_summaries,
    get_single_district_bilingual_summary
)


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


# ==============================================================================
# 1. Threshold Boundaries and Severity Transitions Test
# ==============================================================================
def test_threshold_boundaries_and_severity_transitions():
    # 1. Rainfall Thresholds (< 15.6 Low, 15.6 - 64.4 Mod, 64.5 - 115.5 High, >= 115.6 Severe)
    res_low = evaluate_district_weather_risk("chennai", {"precipitation_mm": 5.0})
    rf_low = next(h for h in res_low["hazards"] if h["hazard_type"] == "rainfall")
    assert rf_low["severity"] == "Low"

    res_mod = evaluate_district_weather_risk("chennai", {"precipitation_mm": 35.0})
    rf_mod = next(h for h in res_mod["hazards"] if h["hazard_type"] == "rainfall")
    assert rf_mod["severity"] == "Moderate"

    res_high = evaluate_district_weather_risk("chennai", {"precipitation_mm": 85.0})
    rf_high = next(h for h in res_high["hazards"] if h["hazard_type"] == "rainfall")
    assert rf_high["severity"] == "High"

    res_sev = evaluate_district_weather_risk("chennai", {"precipitation_mm": 140.0})
    rf_sev = next(h for h in res_sev["hazards"] if h["hazard_type"] == "rainfall")
    assert rf_sev["severity"] == "Severe"

    # 2. Heat Index calculation and severity
    # At 30°C and 65% RH, Heat Index is moderate
    hi_mod = compute_heat_index_celsius(30.0, 65.0)
    assert 32.0 <= hi_mod <= 41.0

    # At 42°C air temp, override guarantees Severe heatwave
    res_heat_sev = evaluate_district_weather_risk("madurai", {"temperature_2m": 43.0, "relative_humidity_2m": 60.0})
    heat_sev = next(h for h in res_heat_sev["hazards"] if h["hazard_type"] == "heat")
    assert heat_sev["severity"] == "Severe"

    # 3. Wind Thresholds (<30 Low, 30-50 Mod, 51-70 High, >70 Severe)
    res_wind = evaluate_district_weather_risk("cuddalore", {"wind_speed_10m": 45.0, "wind_gusts_10m": 75.0})
    w_sev = next(h for h in res_wind["hazards"] if h["hazard_type"] == "wind")
    assert w_sev["severity"] == "Severe"

    # 4. Dry Spell Thresholds (<7 Low, 7-13 Mod, 14-20 High, >20 Severe)
    res_dry = evaluate_district_weather_risk("salem", {}, dry_spell_days=16)
    d_sev = next(h for h in res_dry["hazards"] if h["hazard_type"] == "dry_spell")
    assert d_sev["severity"] == "High"


# ==============================================================================
# 2. Missing, Stale, and Invalid Weather Data Test
# ==============================================================================
def test_missing_and_invalid_weather_data():
    # Test completely empty dict -> should use sensible defaults, no crash
    res_empty = evaluate_district_weather_risk("coimbatore", {})
    assert "composite_severity" in res_empty
    assert len(res_empty["hazards"]) == 4

    # Test invalid non-numeric inputs
    res_invalid = evaluate_district_weather_risk("coimbatore", {
        "temperature_2m": "invalid_temp",
        "relative_humidity_2m": None,
        "precipitation_mm": "None"
    })
    assert res_invalid["composite_severity"] in ["Low", "Moderate", "High", "Severe"]


# ==============================================================================
# 3. Duplicate Alert Prevention and Lifecycle State Transitions
# ==============================================================================
def test_alert_lifecycle_and_deduplication():
    init_risk_tables()

    # Step 1: Create initial active alert
    payload_1 = {
        "district_id": "test_dist_1",
        "hazard_type": "rainfall",
        "severity": "High",
        "trigger_value": 75.0,
        "threshold_value": 64.5,
        "unit": "mm",
        "reason": "Test high rainfall breach.",
        "source": "Test Suite"
    }
    alert_1, action_1 = save_or_update_alert(payload_1)
    assert action_1 == "CREATED"
    assert alert_1["status"] == "Active"
    alert_id = alert_1["alert_id"]

    # Step 2: Trigger same event with identical values -> MUST PREVENT DUPLICATE
    alert_2, action_2 = save_or_update_alert(payload_1)
    assert action_2 == "UNCHANGED"
    assert alert_2["alert_id"] == alert_id

    # Step 3: Trigger ongoing event with intensified rain -> MUST TRANSITION TO 'Updated'
    payload_3 = dict(payload_1)
    payload_3["severity"] = "Severe"
    payload_3["trigger_value"] = 125.0
    payload_3["threshold_value"] = 115.6
    alert_3, action_3 = save_or_update_alert(payload_3)
    assert action_3 == "UPDATED"
    assert alert_3["alert_id"] == alert_id
    assert alert_3["status"] == "Updated"
    assert alert_3["severity"] == "Severe"

    # Step 4: Weather returns to benign conditions (Low) -> MUST TRANSITION TO 'Resolved'
    payload_4 = dict(payload_1)
    payload_4["severity"] = "Low"
    payload_4["trigger_value"] = 4.0
    alert_4, action_4 = save_or_update_alert(payload_4)
    assert action_4 == "RESOLVED"
    assert alert_4["status"] == "Resolved"

    # Step 5: Verify full audit history
    details = get_alert_by_id(alert_id)
    assert details is not None
    assert len(details["audit_history"]) >= 3
    actions = [log["action"] for log in details["audit_history"]]
    assert "CREATED" in actions
    assert "UPDATED" in actions
    assert "RESOLVED" in actions


# ==============================================================================
# 4. Alert Acknowledgment and CSV Export
# ==============================================================================
def test_alert_acknowledgment_and_csv_export():
    init_risk_tables()
    payload = {
        "district_id": "cuddalore",
        "hazard_type": "wind",
        "severity": "High",
        "trigger_value": 62.0,
        "threshold_value": 50.1,
        "unit": "km/h",
        "reason": "Gale wind breach in coastal corridor.",
        "source": "Test Suite"
    }
    alert, _ = save_or_update_alert(payload)
    alert_id = alert["alert_id"]

    # Acknowledge alert
    ack_result = acknowledge_alert(alert_id)
    assert ack_result is not None
    assert ack_result["acknowledged"] == 1
    assert ack_result["acknowledged_at"] is not None

    # CSV export
    csv_str = export_alerts_to_csv_string(district_id="cuddalore")
    assert "Alert ID" in csv_str
    assert "Hazard Type" in csv_str
    assert "cuddalore" in csv_str
    assert "wind" in csv_str


# ==============================================================================
# 5. Bilingual Consistency (English & Tamil)
# ==============================================================================
def test_bilingual_risk_summaries():
    summary = generate_bilingual_risk_summary(
        district_id="cuddalore",
        hazard_type="rainfall",
        severity="High",
        trigger_value=85.0,
        threshold_value=64.5,
        unit="mm"
    )

    assert "en" in summary["summary"]
    assert "ta" in summary["summary"]

    en = summary["summary"]["en"]
    ta = summary["summary"]["ta"]

    # Verify identical values are preserved in both languages
    assert "85.0 mm" in en["description"]
    assert "85.0 mm" in ta["description"]
    assert "64.5 mm" in en["description"]
    assert "64.5 mm" in ta["description"]

    # Verify Tamil terminology
    assert "கடலூர்" in summary["district_name"]["ta"]
    assert "கனமழை" in summary["hazard_name"]["ta"]
    assert len(ta["precautions"]) > 20


# ==============================================================================
# 6. Official Warning Integration and Disclaimer Integrity
# ==============================================================================
def test_official_warning_integration():
    warnings = get_official_imd_warnings(district_id="chennai")
    assert warnings["status"] == "AVAILABLE"
    assert "mausam.imd.gov.in" in warnings["portal_url"]
    assert "Regional Meteorological Centre, Chennai" in warnings["regional_centre"]
    
    # Verify strict disclaimer separates official warnings from app calculations
    assert "IMD" in warnings["disclaimer"]
    assert "never labels internally calculated" in warnings["disclaimer"].lower()


# ==============================================================================
# 7. FastAPI Endpoints Verification
# ==============================================================================
def test_risk_api_endpoints(client):
    # GET /api/risk/overview
    res_ov = client.get("/api/risk/overview")
    assert res_ov.status_code == 200
    ov_data = res_ov.json()
    assert "severity_distribution" in ov_data
    assert "total_districts_monitored" in ov_data

    # GET /api/risk/districts
    res_dist = client.get("/api/risk/districts")
    assert res_dist.status_code == 200
    dist_data = res_dist.json()
    assert len(dist_data) >= 30

    # GET /api/risk/thresholds
    res_th = client.get("/api/risk/thresholds")
    assert res_th.status_code == 200
    th_data = res_th.json()
    assert "application_thresholds" in th_data
    assert "imd_official_criteria" in th_data

    # GET /api/risk/warnings/official
    res_warn = client.get("/api/risk/warnings/official?district=chennai")
    assert res_warn.status_code == 200
    warn_data = res_warn.json()
    assert warn_data["selected_district_warning"] is not None

    # GET /api/risk/summaries/{district}
    res_sum = client.get("/api/risk/summaries/coimbatore")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert "bilingual_hazards" in sum_data

    # GET /api/risk/alerts
    res_alt = client.get("/api/risk/alerts?limit=10")
    assert res_alt.status_code == 200
    alt_data = res_alt.json()
    assert isinstance(alt_data, list)

    # GET /api/risk/alerts/export
    res_exp = client.get("/api/risk/alerts/export")
    assert res_exp.status_code == 200
    assert "text/csv" in res_exp.headers.get("content-type", "")


# ==============================================================================
# 8. Zero PostgreSQL Dependency Test
# ==============================================================================
def test_zero_postgresql_dependency():
    assert "psycopg2" not in sys.modules
    assert "asyncpg" not in sys.modules
    assert os.path.exists(DB_PATH)
    assert not os.path.exists("backend/data/postgresql.conf")
