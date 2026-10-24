"""Unit tests for the Intelligent Location-Aware Early-Warning System (Tamil Nadu & India)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.early_warning import EarlyWarningEngine
from app.services.alert_dispatcher import AlertDispatcher

client = TestClient(app)


def test_lightning_and_thunderstorm_hazard_evaluation():
    # Test high convective conditions triggering warning
    lightning = EarlyWarningEngine.evaluate_lightning_risk(
        precipitation_sum_24h=35.0,
        current_temp_c=34.0,
        relative_humidity=80.0,
        wind_gust_kmh=55.0,
    )
    assert lightning["level"] >= 2
    assert "30-30 Rule" in " ".join(lightning["instructions"])
    assert lightning["risk_score_pct"] > 50.0

    # Test mild thunderstorm conditions
    ts = EarlyWarningEngine.evaluate_thunderstorm_risk(
        precipitation_sum_24h=4.0,
        wind_gust_kmh=20.0,
        wind_speed_kmh=10.0,
    )
    assert ts["level"] == 0
    assert "Informational" in ts["severity_label"]


def test_heavy_rainfall_and_flood_risk_imd_thresholds():
    # Extremely heavy rainfall test (> 204.4 mm in 24h)
    heavy_precip = [10.0] * 24  # 240 mm in 24h
    res = EarlyWarningEngine.evaluate_heavy_rainfall_and_flood("chennai", heavy_precip)
    assert res["level"] == 3
    assert res["severity_label"] == "Emergency"
    assert "Extremely Heavy Rainfall" in res["imd_category"]
    assert "accumulations_mm" in res
    assert res["accumulations_mm"]["24h"] == 240.0

    # Light rain test
    light_precip = [0.1] * 24
    res_light = EarlyWarningEngine.evaluate_heavy_rainfall_and_flood("chennai", light_precip)
    assert res_light["level"] == 0


def test_landslide_susceptibility_nilgiris_vs_chennai():
    # Mountainous district: Nilgiris under heavy antecedent rain
    ls_nilgiris = EarlyWarningEngine.evaluate_landslide_risk(
        location_id="district-nilgiris",
        p_24h_mm=120.0,
        p_72h_antecedent_mm=180.0,
    )
    assert ls_nilgiris["level"] >= 2
    assert "Critical Landslide Emergency" in ls_nilgiris["status"] or "High Landslide" in ls_nilgiris["status"]
    assert any("Mettupalayam" in g for g in ls_nilgiris["critical_ghats"])

    # Flat coastal plain: Chennai (zero landslide susceptibility)
    ls_chennai = EarlyWarningEngine.evaluate_landslide_risk(
        location_id="chennai",
        p_24h_mm=250.0,
        p_72h_antecedent_mm=300.0,
    )
    assert ls_chennai["level"] == 0
    assert "Inland Plain" in ls_chennai["status"] or "Lowland" in ls_chennai["status"]


def test_tsunami_authoritative_incois_bulletin():
    # Inland location (Coimbatore)
    tsunami_cbe = EarlyWarningEngine.evaluate_tsunami_bulletin("coimbatore")
    assert tsunami_cbe["is_coastal"] is False
    assert tsunami_cbe["level"] == 0

    # Coastal location (Nagapattinam / Chennai) normal baseline
    tsunami_coastal = EarlyWarningEngine.evaluate_tsunami_bulletin("nagapattinam")
    assert tsunami_coastal["is_coastal"] is True
    assert tsunami_coastal["level"] == 0

    # Coastal location with active official INCOIS bulletin
    bulletin = {
        "active": True,
        "level": 3,
        "headline": "INCOIS TSUNAMI THREAT: SUNDA TRENCH EVENT",
        "bulletin_id": "INCOIS-TSU-2026-001",
        "estimated_arrival": "T+30 mins",
    }
    tsunami_warn = EarlyWarningEngine.evaluate_tsunami_bulletin("nagapattinam", active_official_bulletin=bulletin)
    assert tsunami_warn["level"] == 3
    assert tsunami_warn["severity_label"] == "Emergency"
    assert "EVACUATE COASTLINE" in " ".join(tsunami_warn["instructions"])
    assert "No independent ML" in tsunami_warn["critical_note"] or "INCOIS" in tsunami_warn["critical_note"]


def test_alert_dispatcher_duplicate_suppression():
    # First dispatch
    d1 = AlertDispatcher.dispatch_alert(
        hazard="heavy_rainfall",
        level=2,
        location_id="chennai",
        location_name="Chennai",
        headline="Heavy Rainfall Warning in Chennai",
        instructions=["Avoid underpasses."],
    )
    assert d1["suppressed"] is False
    assert "dispatch_id" in d1

    # Immediate duplicate dispatch for same hazard, level, and location
    d2 = AlertDispatcher.dispatch_alert(
        hazard="heavy_rainfall",
        level=2,
        location_id="chennai",
        location_name="Chennai",
        headline="Heavy Rainfall Warning in Chennai",
        instructions=["Avoid underpasses."],
    )
    assert d2["suppressed"] is True
    assert "Duplicate alert suppressed" in d2["suppression_reason"]


def test_api_early_warning_alerts_endpoint():
    res = client.get("/api/v1/early-warning/alerts?location_id=chennai&sim_precip_24h=150.0")
    assert res.status_code == 200
    data = res.json()
    assert "overall_alert" in data
    assert "hazards" in data
    assert "lightning" in data["hazards"]
    assert "thunderstorm" in data["hazards"]
    assert "heavy_rainfall" in data["hazards"]
    assert "landslide" in data["hazards"]
    assert "tsunami" in data["hazards"]


def test_api_regional_overview_tamil_nadu():
    res = client.get("/api/v1/early-warning/regional-overview?state=Tamil+Nadu")
    assert res.status_code == 200
    data = res.json()
    assert data["region"] == "Tamil Nadu"
    assert data["district_count"] > 0
    assert "items" in data
