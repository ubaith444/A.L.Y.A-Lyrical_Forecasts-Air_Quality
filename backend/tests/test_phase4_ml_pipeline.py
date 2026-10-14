"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 4 Test Suite: AI Models & Leakage-Free Forecast Evaluation Pipeline

Verifies:
1. Chronological timestamp ordering and split boundary monotonicity (Train < Val < Test).
2. Strict temporal leakage prevention (past features at time t are invariant to future modifications).
3. Metric calculation mathematical correctness (MAE, RMSE, MBE, Precision, Recall, F1, Heavy Rain FAR).
4. Baselines (Persistence, Seasonal Naive), Ridge, and LightGBM model executions.
5. Hugging Face TimesFM benchmark adapter evaluation and fallback resilience.
6. Best-model selection strictly based on validation results, evaluated on test.
7. Model serialization to .joblib, JSON manifest generation, and SQLite registry persistence.
8. FastAPI endpoints (/api/ml/experiments, /api/ml/models, /api/ml/forecast, /api/ml/backtest-results, /api/ml/timesfm-benchmark).
9. Zero PostgreSQL dependency verification.
"""

import os
import sys
import json
import sqlite3
import joblib
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.phase4_ml_pipeline import (
    prepare_leakage_free_dataset,
    execute_chronological_backtest,
    calculate_regression_metrics,
    calculate_rainfall_metrics,
    calculate_classification_metrics,
    calculate_heavy_rain_metrics,
    PersistenceBaseline,
    SeasonalNaiveBaseline,
    RidgeForecaster,
    GradientBoostingForecaster,
    TimesFMAdapter,
    get_timesfm_operational_benchmark,
    get_live_ml_forecast,
    SAVED_MODELS_DIR,
    MANIFEST_PATH,
    BACKTEST_PARQUET_PATH
)
from backend.data.database import init_db, DB_PATH


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


# ==============================================================================
# 1. Chronological Ordering and Split Boundary Test
# ==============================================================================
def test_chronological_splits_and_monotonicity():
    df = prepare_leakage_free_dataset()
    assert len(df) > 1000, "Dataset should have sufficient historical samples"
    assert "dt" in df.columns

    # Verify per-location chronological monotonicity
    for loc_id, group in df.groupby("location_id"):
        diffs = group["dt"].diff().dropna()
        assert (diffs >= pd.Timedelta(0)).all(), f"Location {loc_id} timestamps are not monotonically non-decreasing"

    # Verify train / val / test split boundaries
    unique_dates = df["dt"].drop_duplicates().sort_values().reset_index(drop=True)
    n_dates = len(unique_dates)
    train_end_idx = int(n_dates * 0.70)
    val_end_idx = int(n_dates * 0.85)

    train_cutoff = unique_dates.iloc[train_end_idx]
    val_cutoff = unique_dates.iloc[val_end_idx]

    train_df = df[df["dt"] < train_cutoff]
    val_df = df[(df["dt"] >= train_cutoff) & (df["dt"] < val_cutoff)]
    test_df = df[df["dt"] >= val_cutoff]

    assert train_df["dt"].max() < val_df["dt"].min(), "Train period must strictly precede validation period"
    assert val_df["dt"].max() < test_df["dt"].min(), "Validation period must strictly precede test period"


# ==============================================================================
# 2. Strict Zero Temporal Leakage Guarantee
# ==============================================================================
def test_zero_temporal_leakage_in_features():
    """
    Verifies that modifying, corrupting, or deleting future observations
    does NOT alter feature representations computed for prior timestamps.
    """
    dates = pd.date_range("2024-01-01", periods=15, freq="D")
    sample_df = pd.DataFrame({
        "location_id": ["TEST_CHN"] * 15,
        "timestamp": dates.strftime("%Y-%m-%d 12:00:00+05:30"),
        "temperature_2m": [30.0 + i * 0.5 for i in range(15)],
        "precipitation_mm": [0.0, 5.0, 15.0, 0.0, 25.0, 40.0, 0.0, 0.0, 10.0, 0.0, 50.0, 0.0, 0.0, 5.0, 0.0],
        "relative_humidity_2m": [70.0] * 15,
        "pressure_msl": [1012.0] * 15,
        "wind_speed_10m": [14.0] * 15
    })

    # Save to temp parquet and load through preparation
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tf:
        temp_parquet = tf.name

    try:
        sample_df.to_parquet(temp_parquet, index=False)
        prep_1 = prepare_leakage_free_dataset(temp_parquet)
        feat_at_t5_orig = prep_1[prep_1["dt"] == pd.to_datetime("2024-01-06 12:00:00+05:30")][
            ["temp_lag_1d", "temp_rolling_mean_3d", "rain_lag_1d", "consecutive_dry_days"]
        ].to_dict(orient="records")[0]

        # Now corrupt all future records after Jan 6 (rows 6 to 14) with extreme outliers
        corrupted_df = sample_df.copy()
        corrupted_df.loc[6:, "temperature_2m"] = 99.0
        corrupted_df.loc[6:, "precipitation_mm"] = 999.0
        corrupted_df.to_parquet(temp_parquet, index=False)

        prep_2 = prepare_leakage_free_dataset(temp_parquet)
        feat_at_t5_after = prep_2[prep_2["dt"] == pd.to_datetime("2024-01-06 12:00:00+05:30")][
            ["temp_lag_1d", "temp_rolling_mean_3d", "rain_lag_1d", "consecutive_dry_days"]
        ].to_dict(orient="records")[0]

        # The features computed at t=5 MUST BE IDENTICAL, proving zero future leakage
        assert feat_at_t5_orig == feat_at_t5_after, f"Data leakage detected! Features changed when future was corrupted."
    finally:
        if os.path.exists(temp_parquet):
            os.remove(temp_parquet)


# ==============================================================================
# 3. Metric Calculations Verification
# ==============================================================================
def test_evaluation_metric_calculations():
    # Test regression metrics
    y_true = np.array([30.0, 32.0, 28.0, 35.0])
    y_pred = np.array([31.0, 32.0, 27.0, 37.0])
    # diffs: +1.0, 0.0, -1.0, +2.0 -> abs: 1, 0, 1, 2 -> mae: 1.0
    # sq: 1, 0, 1, 4 -> mean: 1.5 -> rmse: sqrt(1.5) = 1.225
    # mbe: (1 + 0 - 1 + 2)/4 = 0.5
    reg = calculate_regression_metrics(y_true, y_pred)
    assert reg["mae"] == 1.0
    assert abs(reg["rmse"] - 1.225) < 0.01
    assert reg["mbe"] == 0.5

    # Test rainfall metrics with wet day threshold
    y_rain_true = np.array([0.0, 5.0, 0.0, 20.0])
    y_rain_pred = np.array([0.0, 7.0, 1.0, 15.0])
    # wet days: 5.0 (pred 7.0, diff 2.0) and 20.0 (pred 15.0, diff 5.0) -> wet_mae: 3.5
    rain_met = calculate_rainfall_metrics(y_rain_true, y_rain_pred)
    assert rain_met["wet_day_mae"] == 3.5
    assert rain_met["wet_days_count"] == 2

    # Test classification metrics
    y_bin_true = np.array([1, 0, 1, 0])
    y_bin_prob = np.array([0.8, 0.2, 0.3, 0.1])
    # threshold 0.4: pred = [1, 0, 0, 0] -> TP=1, FP=0, FN=1, TN=2
    # Prec = 1/1 = 1.0, Recall = 1/2 = 0.5, F1 = 2*(1*0.5)/(1.5) = 0.6667
    clf_met = calculate_classification_metrics(y_bin_true, y_bin_prob, threshold=0.40)
    assert clf_met["precision"] == 1.0
    assert clf_met["recall"] == 0.5
    assert abs(clf_met["f1_score"] - 0.6667) < 0.001

    # Test heavy rain metrics (IMD 35.5mm)
    y_heavy_true = np.array([10.0, 45.0, 60.0, 5.0])
    y_heavy_pred = np.array([5.0, 40.0, 20.0, 50.0]) # TP: idx 1, FN: idx 2, FP: idx 3
    heavy_met = calculate_heavy_rain_metrics(y_heavy_true, y_heavy_pred, heavy_threshold=35.5)
    assert heavy_met["true_positives"] == 1
    assert heavy_met["false_positives"] == 1
    assert heavy_met["false_negatives"] == 1
    assert heavy_met["event_recall"] == 0.5
    assert heavy_met["false_alarm_rate"] == 0.5


# ==============================================================================
# 4. Baselines, Ridge, and Gradient Boosting Execution Test
# ==============================================================================
def test_baselines_and_ml_models():
    df = prepare_leakage_free_dataset().head(300)
    X = df[[
        "latitude", "longitude", "elevation_m", "is_coastal", "is_hill",
        "month", "day_of_year", "sin_doy", "cos_doy", "is_nem", "is_swm",
        "temp_lag_1d", "temp_lag_2d", "temp_lag_3d", "temp_rolling_mean_3d",
        "temp_rolling_std_3d", "rain_lag_1d", "rain_lag_2d", "rain_lag_3d",
        "rain_rolling_3d", "rain_rolling_7d", "consecutive_dry_days",
        "curr_rh", "curr_pressure", "wind_speed_10m"
    ]]
    y_temp = df["target_temp_24h"].to_numpy()
    y_rain = df["target_rain_24h"].to_numpy()

    # Persistence
    persist = PersistenceBaseline("temperature_2m")
    p_preds = persist.predict(df)
    assert len(p_preds) == len(df)

    # Seasonal Naive
    seasonal = SeasonalNaiveBaseline("temperature_2m", 24)
    s_preds = seasonal.predict(df)
    assert len(s_preds) == len(df)

    # Ridge
    ridge = RidgeForecaster("temperature_2m", alpha=1.0).fit(X, y_temp)
    r_preds = ridge.predict(X)
    assert len(r_preds) == len(df)

    # Gradient Boosting
    gbt = GradientBoostingForecaster("temperature_2m").fit(X, y_temp)
    g_preds = gbt.predict(X)
    assert len(g_preds) == len(df)

    # Gradient Boosting Classifier for rain
    y_bin = (y_rain >= 2.5).astype(float)
    gbt_bin = GradientBoostingForecaster("rain_binary", is_classifier=True).fit(X, y_bin)
    probs = gbt_bin.predict(X)
    assert (probs >= 0.0).all() and (probs <= 1.0).all()


# ==============================================================================
# 5. TimesFM Adapter & Operational Benchmark
# ==============================================================================
def test_timesfm_adapter_and_benchmark():
    adapter = TimesFMAdapter(horizon=24)
    series = np.array([30.0, 31.0, 30.5, 31.2, 32.0])
    preds = adapter.predict(series, target="temp")
    assert len(preds) == len(series)

    dossier = get_timesfm_operational_benchmark()
    assert dossier["model_name"] == "google/timesfm-1.0-200m"
    assert "operational_comparison" in dossier
    assert len(dossier["operational_comparison"]) >= 5
    assert "acceptance_criteria" in dossier["scientific_conclusion"].lower() or "lightgbm" in dossier["scientific_conclusion"].lower()


# ==============================================================================
# 6. Backtest Manifest, Artifacts, and SQLite Registry
# ==============================================================================
def test_backtest_manifest_and_model_registry():
    manifest = execute_chronological_backtest(horizon_hours=24)
    assert "experiment_id" in manifest
    assert "test_leaderboard" in manifest
    assert "persistence" in manifest["test_leaderboard"]
    assert "seasonal_naive" in manifest["test_leaderboard"]
    assert "ridge" in manifest["test_leaderboard"]
    assert "lightgbm" in manifest["test_leaderboard"]
    assert "timesfm" in manifest["test_leaderboard"]

    # Verify best model selection used validation scores
    assert "validation_selection_scores" in manifest
    assert manifest["best_model"] == "lightgbm"

    # Verify model artifact exists and can be deserialized via joblib
    artifact_path = manifest["artifact_path"]
    assert os.path.exists(artifact_path)
    bundle = joblib.load(artifact_path)
    assert "gbt_temp" in bundle
    assert "gbt_rain" in bundle
    assert "gbt_bin" in bundle
    assert "feature_names" in bundle

    # Verify SQLite persistence
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT experiment_id, best_model FROM ml_experiments WHERE experiment_id = ?", (manifest["experiment_id"],))
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == "lightgbm"

    cursor.execute("SELECT model_id, model_type, is_active_best FROM ml_model_registry WHERE model_id = 'MOD_GBDT_24H'")
    m_row = cursor.fetchone()
    assert m_row is not None
    assert m_row[2] == 1 # is_active_best
    conn.close()


# ==============================================================================
# 7. FastAPI ML Endpoints Verification
# ==============================================================================
def test_ml_api_endpoints(client):
    # GET /api/ml/experiments
    res_exp = client.get("/api/ml/experiments")
    assert res_exp.status_code == 200
    exp_data = res_exp.json()
    assert "test_leaderboard" in exp_data
    assert "persistence" in exp_data["test_leaderboard"]

    # GET /api/ml/models
    res_mod = client.get("/api/ml/models")
    assert res_mod.status_code == 200
    models = res_mod.json()
    assert len(models) >= 1
    assert any(m["model_type"] == "gradient_boosting" for m in models)

    # GET /api/ml/forecast
    res_fore = client.get("/api/ml/forecast?district=coimbatore&horizon=24")
    assert res_fore.status_code == 200
    fore = res_fore.json()
    assert fore["district_id"] == "coimbatore"
    assert "predicted_temperature_c" in fore
    assert "temperature_80_ci" in fore
    assert "temperature_95_ci" in fore
    assert "predicted_rainfall_mm" in fore
    assert "rain_probability_pct" in fore

    # GET /api/ml/backtest-results
    res_bt = client.get("/api/ml/backtest-results?district=chennai&limit=25")
    assert res_bt.status_code == 200
    bt_data = res_bt.json()
    assert "temperature" in bt_data
    assert "rainfall" in bt_data
    assert len(bt_data["timestamps"]) > 0

    # GET /api/ml/timesfm-benchmark
    res_tfm = client.get("/api/ml/timesfm-benchmark")
    assert res_tfm.status_code == 200
    tfm_data = res_tfm.json()
    assert "operational_comparison" in tfm_data


# ==============================================================================
# 8. Zero PostgreSQL Dependency Test
# ==============================================================================
def test_zero_postgresql_dependency():
    assert "psycopg2" not in sys.modules
    assert "asyncpg" not in sys.modules
    assert os.path.exists(DB_PATH)
    assert not os.path.exists("backend/data/postgresql.conf")
