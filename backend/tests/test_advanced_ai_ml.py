import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.advanced_ai_ml import (
    PIMLEngine,
    DownscalingEngine,
    DataAssimilationEngine,
    AutoregressiveCorrectionEngine,
    EarthSystemEmulator,
    ProbabilisticEngine,
    NaturalLanguageWeatherIntelligence,
)

client = TestClient(app)


def test_piml_physics_engine():
    res = PIMLEngine.evaluate_physical_consistency(
        temperature_c=32.0,
        relative_humidity_pct=75.0,
        surface_pressure_hpa=1010.0,
        elevation_m=10.0,
        wind_speed_kmh=15.0,
    )
    assert "physics_consistency_score" in res
    assert res["is_physically_plausible"] is True
    assert "saturation_vapor_pressure_hpa" in res

    comp = PIMLEngine.compare_pure_ml_vs_piml(
        base_temp=31.5,
        base_humidity=78.0,
        elevation_m=12.0,
    )
    assert comp["piml"]["physical_consistency_score"] > comp["pure_ml"]["physical_consistency_score"]
    assert "physics_loss_formulation" in comp


def test_downscaling_engine():
    res = DownscalingEngine.downscale_grid(
        coarse_temp=30.0,
        coarse_precip=10.0,
        base_elevation_m=10.0,
        target_elevation_m=500.0,
        distance_to_coast_km=25.0,
        land_use="dense_forest",
    )
    assert "downscaled_result" in res
    assert res["downscaled_result"]["temperature_c"] < 30.0  # Due to lapse rate & forest
    assert res["adjustments"]["orographic_lapse_c"] < 0


def test_data_assimilation_engine():
    res = DataAssimilationEngine.get_multimodal_state(
        latitude=13.0827,
        longitude=80.2707,
        nwp_temp=31.5,
        nwp_rh=76.0,
        nwp_precip=12.0,
    )
    assert "assimilated_state" in res
    assert len(res["data_sources_fused"]) == 5
    assert sum(s["weight_pct"] for s in res["data_sources_fused"]) == 100


def test_autoregressive_correction():
    res = AutoregressiveCorrectionEngine.compute_residual_correction(
        raw_forecast_temp=33.5,
        raw_forecast_rain=20.0,
        lead_time_hours=24,
        season="Northeast Monsoon",
    )
    assert "corrected_forecast" in res
    assert "bias_correction" in res
    assert res["evaluation_metrics"]["data_leakage_prevented"] is True


def test_earth_system_emulator():
    res = EarthSystemEmulator.emulate_couplings(
        atmosphere_temp=32.0,
        rainfall_24h_mm=15.0,
        wind_speed_kmh=12.0,
        coastal_proximity_km=10.0,
    )
    assert "subsystems" in res
    assert "atmosphere" in res["subsystems"]
    assert "hydrology" in res["subsystems"]
    assert "ocean" in res["subsystems"]


def test_probabilistic_engine():
    res = ProbabilisticEngine.compute_probabilistic_outlook(
        deterministic_temp=32.0,
        deterministic_rain=15.0,
    )
    assert "precipitation_exceedance_probabilities" in res
    assert "temperature_prediction_intervals" in res
    assert len(res["ensemble_members"]) == 10


def test_natural_language_intelligence():
    # Test query 1
    q1 = NaturalLanguageWeatherIntelligence.answer_query(
        query="What is the probability of heavy rain in Chennai tomorrow?",
        location_id="chennai",
        current_temp=31.0,
        daily_rain_mm=12.0,
        max_rain_prob=72,
    )
    assert "heavy rainfall" in q1["answer"].lower() or "probability" in q1["answer"].lower()
    assert "data_provenance" in q1

    # Test query 2
    q2 = NaturalLanguageWeatherIntelligence.answer_query(
        query="Why is this district warmer than its surroundings?",
        location_id="chennai",
        current_temp=32.5,
        daily_rain_mm=0.0,
        max_rain_prob=10,
    )
    assert "warmer" in q2["answer"].lower() or "urban heat island" in q2["answer"].lower()

    # Test query 3
    q3 = NaturalLanguageWeatherIntelligence.answer_query(
        query="Compare this monsoon season with historical averages.",
        location_id="chennai",
        current_temp=30.0,
        daily_rain_mm=40.0,
        max_rain_prob=80,
    )
    assert "baseline" in q3["answer"].lower() or "era5" in q3["answer"].lower()


def test_advanced_ml_api_endpoints():
    r1 = client.get("/api/v1/advanced-ml/piml-comparison")
    assert r1.status_code == 200
    assert "piml" in r1.json()

    r2 = client.get("/api/v1/advanced-ml/downscaling")
    assert r2.status_code == 200
    assert "downscaled_result" in r2.json()

    r3 = client.get("/api/v1/advanced-ml/data-assimilation")
    assert r3.status_code == 200
    assert "assimilated_state" in r3.json()

    r4 = client.get("/api/v1/advanced-ml/autoregressive-correction")
    assert r4.status_code == 200
    assert "corrected_forecast" in r4.json()

    r5 = client.get("/api/v1/advanced-ml/earth-system")
    assert r5.status_code == 200
    assert "subsystems" in r5.json()

    r6 = client.get("/api/v1/advanced-ml/probabilistic")
    assert r6.status_code == 200
    assert "precipitation_exceedance_probabilities" in r6.json()

    r7 = client.post(
        "/api/v1/advanced-ml/nlp-query",
        json={"query": "What is the probability of heavy rain in Chennai tomorrow?", "location_id": "chennai"},
    )
    assert r7.status_code == 200
    assert "answer" in r7.json()

    r8 = client.get("/api/v1/advanced-ml/data-sources-matrix")
    assert r8.status_code == 200
    assert len(r8.json()["data_sources"]) >= 7

    r9 = client.get("/api/v1/advanced-ml/regional-multimodal?region_id=tamil_nadu_coast")
    assert r9.status_code == 200
    assert "Coromandel" in r9.json()["name"]
    assert "regional_transfer_mae_c" in r9.json()

    r10 = client.get("/api/v1/advanced-ml/air-quality-intelligence")
    assert r10.status_code == 200
    assert "forecast_naqi" in r10.json()
    assert "ventilation_coefficient_m2s" in r10.json()["meteorological_dispersion"]

    r11 = client.get("/api/v1/advanced-ml/horizon-strategy")
    assert r11.status_code == 200
    assert len(r11.json()["horizons"]) == 4

    r12 = client.get("/api/v1/advanced-ml/model-evaluation-drift?location_id=chennai")
    assert r12.status_code == 200
    assert len(r12.json()["benchmark_comparisons"]) == 4
    assert "drift_and_freshness_monitoring" in r12.json()

    r13 = client.get("/api/v1/advanced-ml/architecture-layers")
    assert r13.status_code == 200
    assert len(r13.json()["layers"]) == 5
