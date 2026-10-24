"""Unit tests for the 3 Prediction Systems:

System A: Operational Weather Forecast Calibration
System B: Extreme-Weather & Climate Anomaly Detection
System C: Long-Term Climate Projections (INDRA-CMIP6)
"""

from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.ml_calibration import WeatherCalibrationEngine
from app.services.anomaly_detector import ClimateAnomalyEngine
from app.services.climate_projections import ClimateProjectionService

client = TestClient(app)


def test_system_a_operational_calibration():
    # Unit test calibration engine
    point = WeatherCalibrationEngine.calibrate_hourly_point(
        location_id="chennai",
        lead_hour=1,
        raw_temperature=32.0,
        raw_precipitation=1.2,
        raw_precip_prob=60.0,
    )
    assert "calibrated_temperature_c" in point
    assert "prediction_interval_10pctl_c" in point
    assert "prediction_interval_90pctl_c" in point
    assert point["prediction_interval_10pctl_c"] < point["calibrated_temperature_c"]
    assert point["calibrated_temperature_c"] < point["prediction_interval_90pctl_c"]
    assert point["calibrated_precipitation_probability_pct"] > 0


def test_system_b_anomaly_detection_and_trend_separation():
    # Episodic spike test (Z >= 2.5)
    diag_spike = ClimateAnomalyEngine.diagnose_anomaly(
        location_id="chennai",
        current_temp_c=38.5,  # May normal is 33.3, departure +5.2°C -> Z > 3.0
        rainfall_month_mm=10.0,
        consecutive_dry_days=12,
        month=5,
        target_date=date(2024, 5, 15),
    )
    assert diag_spike["system"].startswith("System B")
    assert diag_spike["event_vs_trend_diagnosis"]["classification"] == "Episodic Extreme Weather Spike"
    assert diag_spike["event_vs_trend_diagnosis"]["is_climate_trend"] is False

    # Moderate seasonal shift test
    diag_trend = ClimateAnomalyEngine.diagnose_anomaly(
        location_id="chennai",
        current_temp_c=35.0,  # ~1.2-1.5 sigma
        rainfall_month_mm=15.0,
        consecutive_dry_days=25,
        month=5,
        target_date=date(2024, 5, 15),
    )
    assert "Compound Seasonal Deviation" in diag_trend["event_vs_trend_diagnosis"]["classification"]
    assert diag_trend["event_vs_trend_diagnosis"]["is_climate_trend"] is True


def test_system_c_climate_projections():
    proj = ClimateProjectionService.get_projections("chennai")
    assert proj["system"].startswith("System C")
    assert "scenarios" in proj
    assert "ssp126" in proj["scenarios"]
    assert "ssp585" in proj["scenarios"]

    ssp245_epochs = proj["scenarios"]["ssp245"]["epochs"]
    assert "2021_2040" in ssp245_epochs
    assert "2041_2060" in ssp245_epochs
    assert "2081_2100" in ssp245_epochs

    # Check uncertainty spread: p10 < median < p90
    delta = ssp245_epochs["2041_2060"]["temp_delta_c"]
    assert delta["p10"] < delta["median"] < delta["p90"]


def test_api_systems_overview():
    res = client.get("/api/v1/ml/systems")
    assert res.status_code == 200
    data = res.json()
    assert len(data["systems"]) == 3
    ids = [s["id"] for s in data["systems"]]
    assert ids == ["system_a", "system_b", "system_c"]


def test_api_anomalies_endpoint():
    res = client.get("/api/v1/ml/anomalies?location_id=chennai&temp=36.0&dry_days=10&month=5")
    assert res.status_code == 200
    data = res.json()
    assert "composite_anomaly_score" in data
    assert "temperature_anomaly" in data
    assert "event_vs_trend_diagnosis" in data


def test_api_projections_endpoint():
    res = client.get("/api/v1/ml/projections?location_id=chennai&scenario=ssp245")
    assert res.status_code == 200
    data = res.json()
    assert "historical_baseline" in data
    assert "scenarios" in data
    assert "ssp245" in data["scenarios"]
