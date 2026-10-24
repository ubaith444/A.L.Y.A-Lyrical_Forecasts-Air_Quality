import json
import math
import os
import pickle
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.core.database import Database
from app.core.errors import ApiError


class WeatherModelTrainer:
    def __init__(self, database: Database, models_dir: Path):
        self.database = database
        self.models_dir = models_dir
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def split_chronological(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        persistence: pd.Series,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
    ) -> dict[str, Any]:
        """Splits time series chronologically into train, validation, and test partitions.

        Strict rules:
        - Shuffling is strictly disallowed to prevent lookahead data leakage.
        - Train slice strictly precedes Validation slice.
        - Validation slice strictly precedes Test slice.
        """
        n = len(X)
        if n < 50:
            raise ValueError(f"Dataset has only {n} samples; at least 50 valid time-series samples required for modeling.")

        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        X_train, y_train, p_train = X.iloc[:train_end], y.iloc[:train_end], persistence.iloc[:train_end]
        X_val, y_val, p_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end], persistence.iloc[train_end:val_end]
        X_test, y_test, p_test = X.iloc[val_end:], y.iloc[val_end:], persistence.iloc[val_end:]

        return {
            "X_train": X_train,
            "y_train": y_train,
            "p_train": p_train,
            "X_val": X_val,
            "y_val": y_val,
            "p_val": p_val,
            "X_test": X_test,
            "y_test": y_test,
            "p_test": p_test,
            "splits": {
                "train_count": len(X_train),
                "val_count": len(X_val),
                "test_count": len(X_test),
                "total_count": n,
            },
        }

    def train_and_evaluate(
        self,
        dataset_id: str,
        location_id: str,
        target_variable: str,
        horizon_hours: int,
        X: pd.DataFrame,
        y: pd.Series,
        persistence: pd.Series,
        feature_names: list[str],
        algorithm: str = "hist_gradient_boosting",
        model_name: str | None = None,
    ) -> dict[str, Any]:
        """Trains a regression model, computes holdout metrics against persistence baseline,

        and serializes artifacts.
        """
        partitions = self.split_chronological(X, y, persistence)
        X_train = partitions["X_train"]
        y_train = partitions["y_train"]
        X_test = partitions["X_test"]
        y_test = partitions["y_test"]
        p_test = partitions["p_test"]

        # Select Algorithm
        if algorithm == "hist_gradient_boosting":
            model = HistGradientBoostingRegressor(
                max_iter=150,
                learning_rate=0.08,
                random_state=42,
            )
        elif algorithm == "ridge":
            model = Ridge(alpha=1.0)
        elif algorithm == "random_forest":
            model = RandomForestRegressor(
                n_estimators=50,
                max_depth=10,
                random_state=42,
                n_jobs=-1,
            )
        else:
            raise ApiError(400, "invalid_algorithm", f"Algorithm '{algorithm}' is not supported.")

        # Train model on chronological training window
        model.fit(X_train, y_train)

        # Predictions on holdout test set
        y_pred = model.predict(X_test)

        # Calculate Model Metrics
        test_mae = float(mean_absolute_error(y_test, y_pred))
        test_mse = float(mean_squared_error(y_test, y_pred))
        test_rmse = float(math.sqrt(test_mse))
        test_r2 = float(r2_score(y_test, y_pred))

        # Calculate Persistence Baseline Metrics
        base_mae = float(mean_absolute_error(y_test, p_test))
        base_mse = float(mean_squared_error(y_test, p_test))
        base_rmse = float(math.sqrt(base_mse))
        base_r2 = float(r2_score(y_test, p_test))

        # Skill score vs persistence baseline (% MSE reduction)
        skill_score_pct = 0.0
        if base_mse > 1e-6:
            skill_score_pct = float((1.0 - (test_mse / base_mse)) * 100.0)

        metrics = {
            "mae": round(test_mae, 3),
            "rmse": round(test_rmse, 3),
            "mse": round(test_mse, 3),
            "r2": round(test_r2, 4),
            "skill_score_pct": round(skill_score_pct, 2),
        }

        baseline_metrics = {
            "baseline_type": "chronological_persistence",
            "mae": round(base_mae, 3),
            "rmse": round(base_rmse, 3),
            "mse": round(base_mse, 3),
            "r2": round(base_r2, 4),
        }

        # Model identifier & serialization
        model_id = str(uuid.uuid4())
        name = model_name or f"{location_id}_{target_variable}_{horizon_hours}h_{algorithm}"
        artifact_path = self.models_dir / f"{model_id}.pkl"

        model_payload = {
            "id": model_id,
            "name": name,
            "algorithm": algorithm,
            "target_variable": target_variable,
            "horizon_hours": horizon_hours,
            "feature_names": feature_names,
            "model": model,
            "created_at": datetime.utcnow().isoformat(),
        }

        with artifact_path.open("wb") as f:
            pickle.dump(model_payload, f)

        # Save record in SQLite
        now = datetime.utcnow().isoformat()
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO trained_models (
                    id, name, dataset_id, location_id, target_variable,
                    horizon_hours, algorithm, file_path, train_rows, test_rows,
                    metrics_json, baseline_metrics_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_id,
                    name,
                    dataset_id,
                    location_id,
                    target_variable,
                    horizon_hours,
                    algorithm,
                    str(artifact_path.resolve()),
                    len(X_train),
                    len(X_test),
                    json.dumps(metrics),
                    json.dumps(baseline_metrics),
                    now,
                ),
            )

        return {
            "id": model_id,
            "name": name,
            "dataset_id": dataset_id,
            "location_id": location_id,
            "target_variable": target_variable,
            "horizon_hours": horizon_hours,
            "algorithm": algorithm,
            "metrics": metrics,
            "baseline_metrics": baseline_metrics,
            "splits": partitions["splits"],
            "created_at": now,
        }

    def list_models(self, location_id: str | None = None) -> list[dict[str, Any]]:
        """Lists trained models from SQLite."""
        query = "SELECT * FROM trained_models"
        params: list[Any] = []
        if location_id:
            query += " WHERE location_id = ?"
            params.append(location_id)
        query += " ORDER BY created_at DESC"

        with self.database.connection() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        results = []
        for r in rows:
            item = dict(r)
            item["metrics"] = json.loads(item["metrics_json"])
            item["baseline_metrics"] = json.loads(item["baseline_metrics_json"])
            results.append(item)
        return results

    def get_model(self, model_id: str) -> dict[str, Any]:
        """Loads model metadata from SQLite."""
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM trained_models WHERE id = ?", (model_id,)
            ).fetchone()
        if not row:
            raise ApiError(404, "model_not_found", f"Trained model '{model_id}' was not found.")
        item = dict(row)
        item["metrics"] = json.loads(item["metrics_json"])
        item["baseline_metrics"] = json.loads(item["baseline_metrics_json"])
        return item

    def predict(self, model_id: str, input_features: dict[str, float]) -> dict[str, Any]:
        """Executes inference for a single input feature vector."""
        model_meta = self.get_model(model_id)
        artifact_path = Path(model_meta["file_path"])
        if not artifact_path.exists():
            raise ApiError(500, "model_artifact_missing", "Model pickle artifact is missing from disk.")

        with artifact_path.open("rb") as f:
            artifact = pickle.load(f)

        features: list[str] = artifact["feature_names"]
        model = artifact["model"]

        # Validate that all required features are present
        row = []
        missing = []
        for f in features:
            if f in input_features:
                row.append(input_features[f])
            else:
                missing.append(f)

        if missing:
            raise ApiError(
                400,
                "missing_features",
                f"Prediction input is missing required features: {missing[:5]}",
                {"missing_count": len(missing), "examples": missing[:5]},
            )

        X_in = pd.DataFrame([row], columns=features)
        pred = float(model.predict(X_in)[0])

        return {
            "model_id": model_id,
            "name": model_meta["name"],
            "target_variable": model_meta["target_variable"],
            "horizon_hours": model_meta["horizon_hours"],
            "prediction": round(pred, 2),
            "unit": "°C" if "temperature" in model_meta["target_variable"] else "mm",
            "features_used_count": len(features),
        }
