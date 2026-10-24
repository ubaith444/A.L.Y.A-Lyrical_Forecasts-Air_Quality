import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.core.database import Database
from app.main import app
from app.services.ml_features import (
    build_time_series_features,
    load_dataset_parquet,
    save_dataset_parquet_and_csv,
    validate_and_format_hourly_series,
)
from app.services.ml_trainer import WeatherModelTrainer


def generate_synthetic_hourly_series(hours: int = 200) -> dict:
    start = datetime(2023, 1, 1, 0, 0, 0)
    times = [(start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(hours)]
    # Diurnal cycle with trend and noise
    t = np.arange(hours)
    temps = 25.0 + 8.0 * np.sin(2 * np.pi * t / 24.0) + np.random.normal(0, 0.5, hours)
    humidity = 60.0 - 15.0 * np.sin(2 * np.pi * t / 24.0) + np.random.normal(0, 2.0, hours)
    pressure = 1012.0 + 2.0 * np.cos(2 * np.pi * t / 24.0)
    precip = np.where(np.random.rand(hours) > 0.85, np.random.exponential(2.0, hours), 0.0)

    return {
        "time": times,
        "temperature_2m": temps.tolist(),
        "relative_humidity_2m": humidity.tolist(),
        "dew_point_2m": (temps - 5.0).tolist(),
        "precipitation": precip.tolist(),
        "wind_speed_10m": (10.0 + 3.0 * np.sin(t)).tolist(),
        "wind_direction_10m": (180.0 + 45.0 * np.cos(t)).tolist(),
        "surface_pressure": pressure.tolist(),
        "cloud_cover": (40.0 + 20.0 * np.sin(t)).tolist(),
    }


def test_validate_and_format_hourly_series_monotonicity():
    payload = generate_synthetic_hourly_series(50)
    df = validate_and_format_hourly_series(payload, location_id="chennai")
    assert len(df) == 50
    assert "temperature_2m" in df.columns
    assert df["date"].is_monotonic_increasing


def test_validate_rejects_duplicate_timestamps():
    payload = generate_synthetic_hourly_series(20)
    payload["time"][5] = payload["time"][4]  # Introduce duplicate
    with pytest.raises(ValueError, match="duplicate timestamps"):
        validate_and_format_hourly_series(payload, location_id="chennai")


def test_validate_rejects_non_monotonic_timestamps():
    payload = generate_synthetic_hourly_series(20)
    payload["time"][3], payload["time"][4] = payload["time"][4], payload["time"][3]
    with pytest.raises(ValueError, match="strictly monotonically increasing"):
        validate_and_format_hourly_series(payload, location_id="chennai")


def test_parquet_serialization_and_reloading(tmp_path: Path):
    payload = generate_synthetic_hourly_series(100)
    df = validate_and_format_hourly_series(payload, location_id="chennai")

    base = tmp_path / "test_hourly"
    p_path, c_path = save_dataset_parquet_and_csv(df, base)

    assert p_path.exists()
    assert c_path.exists()
    assert p_path.suffix == ".parquet"

    # Load with pyarrow
    loaded_df = load_dataset_parquet(p_path)
    assert len(loaded_df) == 100
    assert "temperature_2m" in loaded_df.columns
    assert (loaded_df["temperature_2m"].round(2) == df["temperature_2m"].round(2)).all()


def test_build_time_series_features_and_lookahead_protection():
    payload = generate_synthetic_hourly_series(150)
    df = validate_and_format_hourly_series(payload, location_id="chennai")

    X, y, persistence, features = build_time_series_features(df, target_variable="temperature_2m", horizon_hours=1)

    assert len(X) == len(y)
    assert len(y) == len(persistence)
    assert len(X) > 100
    assert "temperature_2m_lag_1h" in features
    assert "sin_hour" in features
    assert "cos_hour" in features
    assert "temperature_2m_rolling_6h_mean" in features

    # Check persistence baseline at horizon 1 matches temperature at t
    # and not future target
    assert not np.array_equal(persistence.values, y.values)


def test_chronological_splitting_has_zero_leakage():
    payload = generate_synthetic_hourly_series(200)
    df = validate_and_format_hourly_series(payload, location_id="chennai")
    X, y, persistence, features = build_time_series_features(df, target_variable="temperature_2m", horizon_hours=1)

    trainer = WeatherModelTrainer(Database(Path(":memory:")), Path("/tmp/models"))
    parts = trainer.split_chronological(X, y, persistence, train_ratio=0.7, val_ratio=0.15)

    assert parts["splits"]["train_count"] > parts["splits"]["test_count"]
    # Check strict index monotonicity
    train_indices = parts["X_train"].index
    val_indices = parts["X_val"].index
    test_indices = parts["X_test"].index

    assert train_indices.max() < val_indices.min()
    assert val_indices.max() < test_indices.min()


def test_model_training_and_persistence_benchmark(tmp_path: Path):
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.initialize()

    models_dir = tmp_path / "models"
    trainer = WeatherModelTrainer(db, models_dir)

    payload = generate_synthetic_hourly_series(300)
    df = validate_and_format_hourly_series(payload, location_id="chennai")
    X, y, persistence, features = build_time_series_features(df, target_variable="temperature_2m", horizon_hours=1)

    result = trainer.train_and_evaluate(
        dataset_id="test-dataset-id",
        location_id="chennai",
        target_variable="temperature_2m",
        horizon_hours=1,
        X=X,
        y=y,
        persistence=persistence,
        feature_names=features,
        algorithm="hist_gradient_boosting",
    )

    assert "id" in result
    assert "metrics" in result
    assert "baseline_metrics" in result
    assert result["metrics"]["mae"] >= 0
    assert result["metrics"]["rmse"] >= 0
    assert "skill_score_pct" in result["metrics"]

    # Verify model is listed
    model_list = trainer.list_models()
    assert len(model_list) == 1
    assert model_list[0]["id"] == result["id"]

    # Test inference prediction
    sample_features = {f: float(X.iloc[-1][f]) for f in features}
    pred_res = trainer.predict(result["id"], sample_features)
    assert "prediction" in pred_res
    assert isinstance(pred_res["prediction"], float)


def test_ml_api_endpoints(tmp_path: Path):
    client = TestClient(app)
    # List datasets
    r = client.get("/api/v1/ml/datasets")
    assert r.status_code == 200
    assert "items" in r.json()

    # List models
    r = client.get("/api/v1/ml/models")
    assert r.status_code == 200
    assert "items" in r.json()
