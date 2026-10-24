from datetime import datetime
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd


CORE_HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
    "cloud_cover",
]


def validate_and_format_hourly_series(
    hourly_payload: dict[str, Any],
    location_id: str,
    source: str = "Open-Meteo ERA5-Land",
) -> pd.DataFrame:
    """Validates timestamps and core variables from upstream hourly archive payload.

    Strict rules:
    - Timestamps must be non-empty and formatted as ISO-8601 strings.
    - Timestamps must be unique (no duplicate hours).
    - Series must be strictly monotonically increasing in chronological order.
    - Missing numeric values remain NaN (no artificial fabrication or forward-fill during ingestion).
    """
    times = hourly_payload.get("time")
    if not isinstance(times, list) or len(times) == 0:
        raise ValueError("Hourly payload must contain a non-empty 'time' array.")

    data: dict[str, Any] = {"date": pd.to_datetime(times)}

    # Check for duplicate timestamps
    if len(times) != len(set(times)):
        raise ValueError("Historical hourly series contains duplicate timestamps.")

    # Check chronological monotonicity
    dt_series = pd.Series(data["date"])
    if not dt_series.is_monotonic_increasing:
        raise ValueError("Historical hourly series timestamps must be strictly monotonically increasing.")

    for var in CORE_HOURLY_VARIABLES:
        values = hourly_payload.get(var)
        if isinstance(values, list):
            if len(values) != len(times):
                raise ValueError(f"Variable '{var}' length ({len(values)}) does not match timestamp length ({len(times)}).")
            data[var] = pd.to_numeric(values, errors="coerce")
        else:
            data[var] = np.nan

    data["location_id"] = location_id
    data["source"] = source
    data["retrieved_at"] = datetime.utcnow().isoformat()

    df = pd.DataFrame(data)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def save_dataset_parquet_and_csv(
    df: pd.DataFrame,
    base_path_without_ext: Path,
) -> tuple[Path, Path]:
    """Stores dataset in both Parquet format (for efficient columnar ML) and CSV format."""
    base_path_without_ext.parent.mkdir(parents=True, exist_ok=True)
    parquet_path = base_path_without_ext.with_suffix(".parquet")
    csv_path = base_path_without_ext.with_suffix(".csv")

    # Save to Parquet with pyarrow
    df.to_parquet(parquet_path, engine="pyarrow", index=False)
    # Save to CSV for inspection/export
    df.to_csv(csv_path, index=False)

    return parquet_path, csv_path


def load_dataset_parquet(parquet_path: Path) -> pd.DataFrame:
    """Loads dataset from a Parquet file."""
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    df = pd.read_parquet(parquet_path, engine="pyarrow")
    if "date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def build_time_series_features(
    df: pd.DataFrame,
    target_variable: str = "temperature_2m",
    horizon_hours: int = 1,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, list[str]]:
    """Generates time-series lag features, cyclical calendar features, and rolling aggregates.

    Rules to prevent lookahead data leakage:
    - All rolling stats are computed strictly on past data using .shift(1).
    - Lags are strictly positive (t-1, t-2, t-3, t-6, t-12, t-24).
    - Target is shifted forward by horizon_hours: y[t] = target[t + horizon_hours].
    - Persistence baseline is:
        - for h=1..6h: baseline = current value at t (df[target_variable])
        - for h=24h: baseline = value at t or diurnal persistence t-24+h

    Returns:
        (X, y, persistence_baseline, feature_names)
    """
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    feature_cols: list[str] = []

    # 1. Cyclical Calendar Features
    hours = df["date"].dt.hour
    months = df["date"].dt.month
    day_of_year = df["date"].dt.dayofyear

    df["sin_hour"] = np.sin(2 * np.pi * hours / 24.0)
    df["cos_hour"] = np.cos(2 * np.pi * hours / 24.0)
    df["sin_month"] = np.sin(2 * np.pi * months / 12.0)
    df["cos_month"] = np.cos(2 * np.pi * months / 12.0)
    df["sin_doy"] = np.sin(2 * np.pi * day_of_year / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * day_of_year / 365.25)

    feature_cols.extend(["sin_hour", "cos_hour", "sin_month", "cos_month", "sin_doy", "cos_doy"])

    # Seasonal Indian Climate Flags
    df["is_monsoon"] = months.isin([6, 7, 8, 9]).astype(int)
    df["is_post_monsoon"] = months.isin([10, 11, 12]).astype(int)
    df["is_summer"] = months.isin([3, 4, 5]).astype(int)
    feature_cols.extend(["is_monsoon", "is_post_monsoon", "is_summer"])

    # 2. Lag Features for Target and Physical Predictors
    lag_steps = [1, 2, 3, 6, 12, 24]
    for lag in lag_steps:
        col_name = f"{target_variable}_lag_{lag}h"
        df[col_name] = df[target_variable].shift(lag)
        feature_cols.append(col_name)

    # Core predictor lags (only for variables that actually have valid observations in the dataset)
    other_predictors = [
        v for v in ["relative_humidity_2m", "surface_pressure", "wind_speed_10m", "cloud_cover", "dew_point_2m"]
        if v in df.columns and v != target_variable and df[v].notna().sum() > 20
    ]
    for pred in other_predictors:
        for lag in [1, 3, 6, 24]:
            col_name = f"{pred}_lag_{lag}h"
            df[col_name] = df[pred].shift(lag)
            feature_cols.append(col_name)

    # Barometric pressure tendency (3h pressure delta indicates incoming monsoon depression)
    if "surface_pressure" in df.columns and df["surface_pressure"].notna().sum() > 20:
        df["pressure_tendency_3h"] = df["surface_pressure"].shift(1) - df["surface_pressure"].shift(4)
        feature_cols.append("pressure_tendency_3h")

    # 3. Rolling Statistics (Strictly shifted to prevent lookahead leakage)
    # 6-hour and 24-hour rolling averages and ranges
    target_shifted = df[target_variable].shift(1)
    df[f"{target_variable}_rolling_6h_mean"] = target_shifted.rolling(window=6, min_periods=3).mean()
    df[f"{target_variable}_rolling_24h_mean"] = target_shifted.rolling(window=24, min_periods=12).mean()
    df[f"{target_variable}_rolling_24h_max"] = target_shifted.rolling(window=24, min_periods=12).max()
    df[f"{target_variable}_rolling_24h_min"] = target_shifted.rolling(window=24, min_periods=12).min()
    df[f"{target_variable}_diurnal_range_24h"] = (
        df[f"{target_variable}_rolling_24h_max"] - df[f"{target_variable}_rolling_24h_min"]
    )
    feature_cols.extend([
        f"{target_variable}_rolling_6h_mean",
        f"{target_variable}_rolling_24h_mean",
        f"{target_variable}_rolling_24h_max",
        f"{target_variable}_rolling_24h_min",
        f"{target_variable}_diurnal_range_24h",
    ])

    # Precipitation features if present and populated
    if "precipitation" in df.columns and df["precipitation"].notna().sum() > 20:
        precip_shifted = df["precipitation"].shift(1)
        df["precip_lag_1h"] = precip_shifted
        df["precip_rolling_6h_sum"] = precip_shifted.rolling(window=6, min_periods=2).sum()
        df["precip_rolling_24h_sum"] = precip_shifted.rolling(window=24, min_periods=6).sum()
        df["is_raining_lag_1h"] = (precip_shifted > 0.1).astype(float)
        feature_cols.extend(["precip_lag_1h", "precip_rolling_6h_sum", "precip_rolling_24h_sum", "is_raining_lag_1h"])

    # 4. Target variable shifted forward by horizon
    df["target"] = df[target_variable].shift(-horizon_hours)

    # 5. Persistence Baseline definition:
    # Predict the target at t+horizon using the current observation at time t
    df["persistence_baseline"] = df[target_variable]

    # Only retain feature columns that have sufficient valid values
    active_features = [col for col in feature_cols if col in df.columns and df[col].notna().sum() >= 30]

    # Drop NaN rows generated by lags at the start and forward-shift at the end
    valid_mask = df["target"].notna() & df["persistence_baseline"].notna()
    for col in active_features:
        valid_mask = valid_mask & df[col].notna()

    clean_df = df[valid_mask].reset_index(drop=True)

    X = clean_df[active_features]
    y = clean_df["target"]
    persistence = clean_df["persistence_baseline"]

    return X, y, persistence, active_features
