"""
Tamil Nadu Climate & Forecast Intelligence Platform
Machine Learning Prediction Service

Loads and serves the self-trained Random Forest + Gradient Boosting model:
- Rain occurrence probability (Classification)
- Rainfall depth estimation in mm (Regression)
- Temperature anomaly estimation in °C (Regression)
- Feature extraction based on Tamil Nadu's 15 geographical & climatological indicators
"""

import os
import joblib
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional
import shutil
from backend.data.districts_data import TAMIL_NADU_DISTRICTS
from backend.services.weather_service import fetch_live_weather, get_location_coordinates
from backend.data.database import get_models_dir


def resolve_model_path() -> str:
    """
    Resolves model artifact path respecting persistent DATA_DIR/models/.
    Prevents re-downloading large models on application restarts.
    """
    persistent_models_dir = get_models_dir()
    persistent_model_path = os.path.join(persistent_models_dir, "tn_weather_model.joblib")
    bundled_model_path = os.path.join(os.path.dirname(__file__), "tn_weather_model.joblib")

    # If already in persistent storage, load it
    if os.path.exists(persistent_model_path):
        return persistent_model_path

    # If bundled model exists, seed persistent storage if different path
    if os.path.exists(bundled_model_path):
        if os.path.abspath(persistent_model_path) != os.path.abspath(bundled_model_path):
            try:
                shutil.copy2(bundled_model_path, persistent_model_path)
                return persistent_model_path
            except Exception:
                return bundled_model_path
        return bundled_model_path

    return persistent_model_path


MODEL_PATH = resolve_model_path()


class WeatherPredictor:
    def __init__(self):
        self.model_data = None
        self.clf_rain = None
        self.reg_rain = None
        self.reg_temp = None
        self.feature_names = None
        self._load_model()

    def _load_model(self):
        global MODEL_PATH
        MODEL_PATH = resolve_model_path()
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Trained model not found at {MODEL_PATH}")
        self.model_data = joblib.load(MODEL_PATH)
        self.clf_rain = self.model_data["clf_rain"]
        self.reg_rain = self.model_data["reg_rain"]
        self.reg_temp = self.model_data["reg_temp"]
        self.feature_names = self.model_data["features"]

    def extract_features(self, district_id: str, live_data: Optional[Dict[str, Any]] = None) -> np.ndarray:
        dist_meta = get_location_coordinates(district_id)
        if not dist_meta:
            dist_id_clean = district_id.lower()
            if dist_id_clean in TAMIL_NADU_DISTRICTS:
                d = TAMIL_NADU_DISTRICTS[dist_id_clean]
                dist_meta = {
                    "latitude": d["lat"],
                    "longitude": d["lon"],
                    "elevation_m": d["elevation_m"],
                    "is_coastal": d["is_coastal"]
                }
            else:
                dist_meta = {
                    "latitude": 13.0827,
                    "longitude": 80.2707,
                    "elevation_m": 7.0,
                    "is_coastal": True
                }

        if not live_data:
            try:
                live_data = fetch_live_weather(district_id)
            except Exception:
                live_data = {}

        now = datetime.now()
        doy = now.timetuple().tm_yday
        month = now.month

        # Day of year harmonic seasonality
        sin_doy = np.sin(2 * np.pi * doy / 365.0)
        cos_doy = np.cos(2 * np.pi * doy / 365.0)

        # Monsoon periods
        is_nem = 1.0 if month in (10, 11, 12) else 0.0
        is_swm = 1.0 if month in (6, 7, 8, 9) else 0.0

        curr_temp = float(live_data.get("temperature_2m", 30.5))
        curr_rh = float(live_data.get("relative_humidity_2m", 68.0))
        curr_pressure = float(live_data.get("pressure_msl", 1010.5))
        wind_speed = float(live_data.get("wind_speed_10m", 12.0))
        cloud_cover = float(live_data.get("cloud_cover", 30.0))
        antecedent_rain = float(live_data.get("precipitation_mm", 0.0))

        # Dewpoint depression estimate: (100 - RH) / 5
        dewpoint_dep = max(0.0, (100.0 - curr_rh) / 5.0)

        feature_vector = [
            dist_meta["latitude"],
            dist_meta["longitude"],
            dist_meta["elevation_m"],
            1.0 if dist_meta.get("is_coastal") else 0.0,
            sin_doy,
            cos_doy,
            curr_temp,
            curr_pressure,
            curr_rh,
            dewpoint_dep,
            wind_speed,
            cloud_cover,
            antecedent_rain,
            is_nem,
            is_swm
        ]

        return np.array(feature_vector).reshape(1, -1)

    def predict(self, district_id: str, live_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs ML model inference to produce 24h predictions.
        """
        import pandas as pd
        X = self.extract_features(district_id, live_data)
        X_df = pd.DataFrame(X, columns=self.feature_names)

        # 1. Classification: Rain occurrence probability
        rain_proba = float(self.clf_rain.predict_proba(X_df)[0][1])
        will_rain = bool(rain_proba >= 0.40)

        # 2. Regression: Rain depth (mm)
        rain_mm_raw = float(self.reg_rain.predict(X_df)[0])
        rain_mm = round(max(0.0, rain_mm_raw if will_rain else rain_mm_raw * 0.2), 1)

        # 3. Regression: Temperature anomaly (°C)
        temp_anomaly = round(float(self.reg_temp.predict(X_df)[0]), 2)

        # Feature Importance Insights
        clf_importances = self.clf_rain.feature_importances_
        top_indices = np.argsort(clf_importances)[::-1][:4]
        top_features = [
            {"feature": self.feature_names[i], "importance_weight": round(float(clf_importances[i]), 3)}
            for i in top_indices
        ]

        now_iso = datetime.now().isoformat()

        return {
            "model_identifier": "tn_weather_model_v1.0_ensemble",
            "model_type": "RandomForest Classifier + GradientBoosting Regressors",
            "provenance": "Self-Trained Model (Tamil Nadu Micro-Climate Tuned)",
            "district_id": district_id.lower(),
            "timestamp": now_iso,
            "predictions": {
                "rain_probability_pct": round(rain_proba * 100, 1),
                "will_rain_24h": will_rain,
                "predicted_rain_depth_mm": rain_mm,
                "temperature_anomaly_celsius": temp_anomaly,
                "confidence_level": "High" if abs(rain_proba - 0.5) > 0.25 else "Moderate"
            },
            "key_driving_features": top_features,
            "trained_accuracy_benchmark": {
                "rain_accuracy_pct": 65.87,
                "temp_anomaly_mae": 1.48
            }
        }


# Global Singleton instance
predictor = WeatherPredictor()
