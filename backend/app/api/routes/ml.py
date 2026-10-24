import json
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencies import get_database, get_location_service, get_provider
from app.core.config import get_settings
from app.core.errors import ApiError
from app.services.anomaly_detector import ClimateAnomalyEngine
from app.services.climate_projections import ClimateProjectionService
from app.services.ml_calibration import WeatherCalibrationEngine
from app.services.ml_features import (
    build_time_series_features,
    load_dataset_parquet,
    save_dataset_parquet_and_csv,
    validate_and_format_hourly_series,
)
from app.services.ml_trainer import WeatherModelTrainer
from app.services.providers import OpenMeteoClient

router = APIRouter()


class IngestHourlyRequest(BaseModel):
    location_id: str
    start_date: date
    end_date: date
    models: str = Field(default="era5_land")


class TrainModelRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    dataset_id: str
    target_variable: str = Field(default="temperature_2m")
    horizon_hours: int = Field(default=1, ge=1, le=72)
    algorithm: str = Field(default="hist_gradient_boosting")
    model_name: str | None = None


class PredictRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    features: dict[str, float]


def get_trainer() -> WeatherModelTrainer:
    db = get_database()
    models_dir = get_settings().data_dir / "models"
    return WeatherModelTrainer(db, models_dir)


@router.post("/datasets/ingest-hourly", status_code=201)
async def ingest_hourly_dataset(
    request: IngestHourlyRequest,
    provider: OpenMeteoClient = Depends(get_provider),
) -> dict[str, Any]:
    """Downloads hourly historical weather data (ERA5-Land), validates timestamps,

    and stores as Parquet (for efficient columnar ML) and CSV.
    """
    locations = get_location_service()
    location = locations.get(request.location_id)

    if request.end_date > date.today():
        raise ApiError(422, "invalid_historical_range", "Historical ingestion cannot include future dates.")

    if request.start_date > request.end_date:
        raise ApiError(422, "invalid_dates", "start_date must be before or equal to end_date.")

    # Request hourly data from Open-Meteo Archive
    payload = await provider.archive_hourly(
        latitude=location["latitude"],
        longitude=location["longitude"],
        timezone=location["timezone"],
        start_date=request.start_date.isoformat(),
        end_date=request.end_date.isoformat(),
        models=request.models,
    )

    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or "time" not in hourly:
        raise ApiError(502, "provider_malformed", "Upstream historical response missing 'hourly' series.")

    # Validate timestamps, monotonicity, and format as DataFrame
    try:
        df = validate_and_format_hourly_series(
            hourly_payload=hourly,
            location_id=request.location_id,
            source=f"Open-Meteo ({request.models})",
        )
    except ValueError as e:
        raise ApiError(422, "validation_failed", str(e))

    # Save both Parquet and CSV
    dataset_id = str(uuid.uuid4())
    data_dir = get_settings().data_dir / "historical"
    base_path = data_dir / dataset_id
    parquet_path, csv_path = save_dataset_parquet_and_csv(df, base_path)

    retrieved_at = datetime.utcnow().isoformat()
    metadata = {
        "location": location,
        "models": request.models,
        "resolution": "hourly",
        "variables": [c for c in df.columns if c not in ["date", "location_id", "source", "retrieved_at"]],
        "parquet_path": str(parquet_path.resolve()),
        "csv_path": str(csv_path.resolve()),
        "validation": "Strict monotonic chronological ordering confirmed; duplicates rejected.",
    }

    # Store in SQLite
    db = get_database()
    with db.connection() as conn:
        conn.execute(
            """
            INSERT INTO historical_datasets (
                id, location_id, source, data_kind, file_path,
                start_date, end_date, retrieved_at, row_count, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dataset_id,
                request.location_id,
                f"Open-Meteo {request.models}",
                "reanalysis_hourly",
                str(parquet_path.resolve()),
                request.start_date.isoformat(),
                request.end_date.isoformat(),
                retrieved_at,
                len(df),
                json.dumps(metadata),
            ),
        )

    return {
        "dataset_id": dataset_id,
        "location_id": request.location_id,
        "models": request.models,
        "row_count": len(df),
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "parquet_path": str(parquet_path.name),
        "csv_path": str(csv_path.name),
        "variables": metadata["variables"],
    }


@router.get("/datasets")
async def list_training_datasets(location_id: str | None = None) -> dict[str, Any]:
    """Lists historical datasets available for time series training."""
    db = get_database()
    query = "SELECT * FROM historical_datasets"
    params: list[Any] = []
    if location_id:
        query += " WHERE location_id = ?"
        params.append(location_id)
    query += " ORDER BY retrieved_at DESC"

    with db.connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    items = []
    for r in rows:
        item = dict(r)
        try:
            item["metadata"] = json.loads(item["metadata_json"])
        except Exception:
            item["metadata"] = {}
        # Check parquet existence
        parquet_exists = Path(item["file_path"]).suffix == ".parquet" and Path(item["file_path"]).exists()
        item["has_parquet"] = parquet_exists
        items.append(item)

    return {"items": items}


@router.post("/train", status_code=201)
async def train_model(
    request: TrainModelRequest,
    trainer: WeatherModelTrainer = Depends(get_trainer),
) -> dict[str, Any]:
    """Trains a time series forecasting model on a Parquet dataset,

    evaluates against a chronological persistence baseline, and stores model artifacts.
    """
    db = get_database()
    with db.connection() as conn:
        row = conn.execute("SELECT * FROM historical_datasets WHERE id = ?", (request.dataset_id,)).fetchone()
    if not row:
        raise ApiError(404, "dataset_not_found", f"Dataset '{request.dataset_id}' does not exist.")

    dataset = dict(row)
    file_path = Path(dataset["file_path"])

    # Load from parquet if available, otherwise check for adjacent parquet
    if file_path.suffix != ".parquet":
        alt_parquet = file_path.with_suffix(".parquet")
        if alt_parquet.exists():
            file_path = alt_parquet

    try:
        df = load_dataset_parquet(file_path)
    except Exception as e:
        # Fallback to CSV loading if only CSV exists
        if file_path.with_suffix(".csv").exists():
            import pandas as pd
            df = pd.read_csv(file_path.with_suffix(".csv"))
            df["date"] = pd.to_datetime(df["date"])
        else:
            raise ApiError(500, "dataset_read_error", f"Could not read dataset file: {str(e)}")

    if request.target_variable not in df.columns:
        raise ApiError(
            422,
            "target_variable_missing",
            f"Target variable '{request.target_variable}' not in dataset columns: {list(df.columns)}",
        )

    # Feature Engineering
    try:
        X, y, persistence, feature_names = build_time_series_features(
            df=df,
            target_variable=request.target_variable,
            horizon_hours=request.horizon_hours,
        )
    except Exception as e:
        raise ApiError(422, "feature_engineering_failed", f"Failed generating time series features: {str(e)}")

    # Model Training and Chronological Evaluation
    result = trainer.train_and_evaluate(
        dataset_id=request.dataset_id,
        location_id=dataset["location_id"],
        target_variable=request.target_variable,
        horizon_hours=request.horizon_hours,
        X=X,
        y=y,
        persistence=persistence,
        feature_names=feature_names,
        algorithm=request.algorithm,
        model_name=request.model_name,
    )

    return result


@router.get("/models")
async def list_models(
    location_id: str | None = None,
    trainer: WeatherModelTrainer = Depends(get_trainer),
) -> dict[str, Any]:
    """Lists trained forecasting models and chronological evaluation metrics."""
    models = trainer.list_models(location_id)
    return {"items": models}


@router.post("/predict")
async def predict_forecast(
    request: PredictRequest,
    trainer: WeatherModelTrainer = Depends(get_trainer),
) -> dict[str, Any]:
    """Runs inference on a trained model."""
    return trainer.predict(request.model_id, request.features)


@router.get("/systems")
async def get_prediction_systems_overview() -> dict[str, Any]:
    """Returns scientific overview of the 3 prediction systems:

    System A (Operational weather calibration), System B (Climate anomaly detection),
    and System C (Long-term downscaled climate projections).
    """
    return {
        "design_principle": "Use AI/ML where it adds measurable value—not to train a model that simply extrapolates yesterday's weather into the distant future.",
        "systems": [
            {
                "id": "system_a",
                "name": "System A — Operational Weather Forecasting",
                "phase": "Phase 1",
                "horizon": "1 hour to 14 days",
                "purpose": "Predict temperature, rainfall probability, humidity, wind, and heat conditions for specific upcoming dates.",
                "approach": "NWP baseline (Open-Meteo GFS/ECMWF) with local ML quantile calibration for residual bias correction and uncertainty intervals (p10 to p90).",
                "primary_models": ["HistGradientBoosting", "LightGBM Quantile Regressors", "Logistic Rain Probability"],
                "datasets": ["Open-Meteo Forecast API", "Open-Meteo Historical Forecast API", "ERA5-Land"],
            },
            {
                "id": "system_b",
                "name": "System B — Extreme-Weather and Climate Anomaly Detection",
                "phase": "Phase 2",
                "horizon": "Hourly, daily, monthly, and seasonal",
                "purpose": "Identify unusual heat, cold, rainfall deficits, and dry spells against location-specific historical normals.",
                "approach": "Standardized departures (Z-scores) vs 1991–2020 ERA5-Land climatology and IMD LPA criteria.",
                "critical_distinction": "Explicitly distinguishes episodic weather spikes (synoptic events <5 days) from systemic climate trends / multi-year warming shifts.",
                "primary_models": ["Standardized Climatological Departures (Z-scores)", "Multivariate Isolation Score", "IMD Heatwave & Monsoon Deficit Classifier"],
                "datasets": ["ERA5-Land (1991–2020 Normal)", "IMD Gridded Observations"],
            },
            {
                "id": "system_c",
                "name": "System C — Long-Term Climate Projection",
                "phase": "Phase 3",
                "horizon": "2030s through 2100 (Epochs: 2021–2040, 2041–2060, 2081–2100)",
                "purpose": "Estimate multi-decadal changes in temperature, rainfall distributions, extreme-heat days, and dry spells under 4 emissions pathways.",
                "approach": "Ensemble summaries and statistical downscaling (INDRA-CMIP6 at 0.1° resolution) rather than deterministic daily forecasting.",
                "critical_distinction": "Shows multi-model ensemble medians and 10th–90th percentile spreads across epochs under SSP scenarios (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5). Never claims to know exact weather on a specific day 30 years out.",
                "primary_models": ["INDRA-CMIP6 Multi-Model Ensemble", "BCSD Statistical Downscaling", "Extreme Value Theory"],
                "datasets": ["INDRA-CMIP6 Downscaled Ensemble (0.1° / ~10.5 km)", "CMIP6 Global Ensembles"],
            },
        ],
    }


@router.get("/calibration")
async def get_calibrated_forecast(
    location_id: str = Query(default="chennai"),
    provider: OpenMeteoClient = Depends(get_provider),
) -> dict[str, Any]:
    """System A: Returns operational NWP forecast calibrated with local ML models,

    including 10th/90th percentile prediction intervals and calibrated precipitation probabilities.
    """
    locations = get_location_service()
    location = locations.get(location_id)

    # Ingest fresh operational forecast from Open-Meteo
    raw_payload = await provider.forecast(
        latitude=location["latitude"],
        longitude=location["longitude"],
        timezone=location["timezone"],
        hourly=[
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "precipitation_probability",
            "wind_speed_10m",
            "surface_pressure",
        ],
        daily=["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        forecast_days=7,
    )

    hourly_data = raw_payload.get("hourly", {})
    times = hourly_data.get("time", [])
    temps = hourly_data.get("temperature_2m", [])
    precips = hourly_data.get("precipitation", [])
    precip_probs = hourly_data.get("precipitation_probability", [])
    rhs = hourly_data.get("relative_humidity_2m", [])

    series_input = []
    for i in range(min(len(times), 72)):
        series_input.append({
            "time": times[i],
            "temperature": temps[i] if i < len(temps) else 28.0,
            "precipitation": precips[i] if i < len(precips) else 0.0,
            "precipitation_probability": precip_probs[i] if i < len(precip_probs) else None,
            "relative_humidity": rhs[i] if i < len(rhs) else None,
        })

    return WeatherCalibrationEngine.calibrate_operational_forecast(
        location_id=location_id,
        hourly_forecasts=series_input,
    )


@router.get("/anomalies")
async def get_climate_anomaly_diagnosis(
    location_id: str = Query(default="chennai"),
    temp: float | None = Query(default=None),
    rain_month: float | None = Query(default=None),
    dry_days: int = Query(default=0, ge=0),
    month: int | None = Query(default=None),
) -> dict[str, Any]:
    """System B: Evaluates extreme-weather and climate anomalies against 1991–2020 ERA5-Land baselines,

    and distinguishes episodic synoptic spikes from multi-year climate warming trends.
    """
    if month is None:
        month = date.today().month

    # Defaults based on typical current climate if not passed
    if temp is None:
        normals = ClimateAnomalyEngine.get_location_normals(location_id)
        temp = normals["temperature_mean"].get(str(month), 29.5) + 0.8

    if rain_month is None:
        normals = ClimateAnomalyEngine.get_location_normals(location_id)
        rain_month = normals["rainfall_monthly_mean"].get(str(month), 60.0)

    return ClimateAnomalyEngine.diagnose_anomaly(
        location_id=location_id,
        current_temp_c=temp,
        rainfall_month_mm=rain_month,
        consecutive_dry_days=dry_days,
        month=month,
    )


@router.get("/projections")
async def get_climate_projections(
    location_id: str = Query(default="chennai"),
    scenario: str | None = Query(default=None),
    epoch: str | None = Query(default=None),
) -> dict[str, Any]:
    """System C: Returns multi-decadal INDRA-CMIP6 downscaled climate projections (2021–2100)

    under SSP1-2.6, SSP2-4.5, SSP3-7.0, and SSP5-8.5 scenarios with ensemble spreads.
    """
    return ClimateProjectionService.get_projections(
        location_id=location_id,
        scenario=scenario,
        epoch=epoch,
    )

