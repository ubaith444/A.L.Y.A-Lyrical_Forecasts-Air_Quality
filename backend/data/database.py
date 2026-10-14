"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 1: SQLite Analytical Database, Schema, and Ingestion Logging

Storage Architecture (Section 1.6 & 1.7):
- No PostgreSQL. SQLite handles relational metadata, job audit logs, and cache indices.
- Composite record identity: (location_id, timestamp, source_type, lead_time_hours, forecast_init_time)
  preventing duplicate records on repeat ingestion runs.
- Ingestion audit logs track job status, duration, error category, and record freshness.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from backend.data.locations_registry import CORE_MONITORING_LOCATIONS
from backend.data.districts_data import TAMIL_NADU_DISTRICTS


def get_data_dir() -> str:
    """Returns persistent data directory (defaults to /var/data in prod or backend/data locally)."""
    env_dir = os.environ.get("DATA_DIR")
    if env_dir:
        os.makedirs(env_dir, exist_ok=True)
        return env_dir
    default_dir = os.path.dirname(__file__)
    return default_dir


def get_db_path() -> str:
    """Returns SQLite database path respecting DATABASE_URL or DATA_DIR."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("sqlite:///"):
        # Handle sqlite:////var/data/climate.db or sqlite:///path
        if db_url.startswith("sqlite:////"):
            clean_path = "/" + db_url[11:]
        else:
            clean_path = db_url[10:]
        os.makedirs(os.path.dirname(clean_path), exist_ok=True)
        return clean_path

    data_dir = get_data_dir()
    # In production on Render with DATA_DIR, use climate.db per Phase 6 requirements
    if "DATA_DIR" in os.environ and os.environ.get("DATA_DIR") == "/var/data":
        target = os.path.join(data_dir, "climate.db")
    else:
        target = os.path.join(data_dir, "climate_forecast.db")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    return target


def get_datasets_dir() -> str:
    """Returns path for downloaded/processed historical datasets under persistent storage."""
    data_dir = get_data_dir()
    d_dir = os.path.join(data_dir, "datasets")
    os.makedirs(d_dir, exist_ok=True)
    return d_dir


def get_models_dir() -> str:
    """Returns path for machine learning model artifacts under persistent storage."""
    data_dir = get_data_dir()
    m_dir = os.path.join(data_dir, "models")
    os.makedirs(m_dir, exist_ok=True)
    return m_dir


def get_backups_dir() -> str:
    """Returns path for atomic SQLite backups."""
    data_dir = get_data_dir()
    b_dir = os.path.join(data_dir, "backups")
    os.makedirs(b_dir, exist_ok=True)
    return b_dir


DB_PATH = get_db_path()


def get_db_connection() -> sqlite3.Connection:
    current_path = get_db_path()
    os.makedirs(os.path.dirname(current_path), exist_ok=True)
    conn = sqlite3.connect(current_path)
    conn.row_factory = sqlite3.Row
    return conn


def backup_database(destination_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates an atomic, consistent backup of the SQLite database using SQLite's online backup API.
    Does not copy a live database file blindly; locks a safe, non-corrupted point-in-time snapshot.
    """
    if not destination_path:
        b_dir = get_backups_dir()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination_path = os.path.join(b_dir, f"climate_backup_{ts}.db")
    else:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    src_conn = get_db_connection()
    dst_conn = sqlite3.connect(destination_path)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    size_bytes = os.path.getsize(destination_path) if os.path.exists(destination_path) else 0
    return {
        "status": "SUCCESS",
        "method": "sqlite3_online_backup_api",
        "source_path": get_db_path(),
        "backup_path": destination_path,
        "size_bytes": size_bytes,
        "created_at": datetime.now().isoformat()
    }


def init_db():
    # Ensure persistent directories exist
    get_datasets_dir()
    get_models_dir()
    get_backups_dir()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Locations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        location_id TEXT PRIMARY KEY,
        district_id TEXT UNIQUE,
        name TEXT NOT NULL,
        tamil_name TEXT,
        region TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        elevation_m REAL NOT NULL,
        is_coastal INTEGER DEFAULT 0,
        is_hill INTEGER DEFAULT 0,
        normal_annual_rainfall_mm REAL,
        nem_normal_mm REAL,
        swm_normal_mm REAL,
        primary_crops TEXT,
        critical_reservoirs TEXT,
        agriculture_impact TEXT
    )
    """)

    # 2. Weather Records Table with Composite Identity (Section 1.6)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        timestamp_utc TEXT,
        temperature_2m REAL,
        relative_humidity_2m REAL,
        dew_point_2m REAL,
        precipitation_mm REAL,
        wind_speed_10m REAL,
        wind_direction_10m REAL,
        pressure_msl REAL,
        cloud_cover REAL,
        source_type TEXT NOT NULL, -- 'observation', 'reanalysis', 'forecast', 'climate_model'
        lead_time_hours INTEGER DEFAULT 0,
        forecast_init_time TEXT,
        fetched_at TEXT NOT NULL,
        quality_flag TEXT DEFAULT 'valid', -- 'valid', 'suspicious', 'missing', 'corrected', 'rejected'
        FOREIGN KEY (location_id) REFERENCES locations(location_id),
        UNIQUE(location_id, timestamp, source_type, lead_time_hours, forecast_init_time)
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_weather_composite 
    ON weather_records(location_id, timestamp, source_type, quality_flag)
    """)

    # 3. Live & Forecast Cache (with TTL)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS live_cache (
        cache_key TEXT PRIMARY KEY,
        data_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )
    """)

    # 4. Ingestion Job Audit Logs (Section 1.7)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ingestion_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        source TEXT NOT NULL,
        location_id TEXT,
        status TEXT NOT NULL, -- 'SUCCESS', 'FAILED', 'PARTIAL'
        duration_ms INTEGER,
        records_count INTEGER,
        error_category TEXT,
        error_message TEXT,
        timestamp TEXT NOT NULL
    )
    """)

    # 5. Pipeline Runs Tracking Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT UNIQUE NOT NULL,
        run_type TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        status TEXT NOT NULL,
        locations_count INTEGER,
        records_ingested INTEGER,
        records_quarantined INTEGER,
        duration_ms INTEGER,
        completeness_pct REAL,
        freshness_minutes REAL,
        report_path TEXT
    )
    """)

    # 6. Climate Reports Table (Phase 3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS climate_reports (
        report_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        district_id TEXT NOT NULL,
        start_year INTEGER NOT NULL,
        end_year INTEGER NOT NULL,
        season TEXT NOT NULL,
        variable TEXT NOT NULL,
        pdf_path TEXT,
        csv_path TEXT,
        summary_json TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 7. ML Experiments Table (Phase 4)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ml_experiments (
        experiment_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        target_variable TEXT NOT NULL,
        horizon_hours INTEGER NOT NULL,
        models_evaluated TEXT NOT NULL,
        best_model TEXT NOT NULL,
        train_start TEXT,
        train_end TEXT,
        val_start TEXT,
        val_end TEXT,
        test_start TEXT,
        test_end TEXT,
        metrics_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    # 8. ML Model Registry Table (Phase 4)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ml_model_registry (
        model_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        model_type TEXT NOT NULL,
        target_variable TEXT NOT NULL,
        horizon_hours INTEGER NOT NULL,
        artifact_path TEXT,
        val_mae REAL,
        val_rmse REAL,
        val_f1 REAL,
        test_mae REAL,
        test_rmse REAL,
        test_f1 REAL,
        is_active_best INTEGER DEFAULT 0,
        hyperparameters_json TEXT,
        registered_at TEXT NOT NULL
    )
    """)

    # 9. Risk Alerts Table (Phase 5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_alerts (
        alert_id TEXT PRIMARY KEY,
        district_id TEXT NOT NULL,
        hazard_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        trigger_value REAL NOT NULL,
        threshold_value REAL NOT NULL,
        unit TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL,
        acknowledged INTEGER DEFAULT 0,
        acknowledged_at TEXT,
        previous_value REAL,
        source TEXT NOT NULL,
        summary_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        resolved_at TEXT
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_risk_alerts_query
    ON risk_alerts(district_id, hazard_type, severity, status)
    """)

    # 10. Alert Audit Log Table (Phase 5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alert_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id TEXT NOT NULL,
        action TEXT NOT NULL,
        old_severity TEXT,
        new_severity TEXT,
        old_value REAL,
        new_value REAL,
        timestamp TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (alert_id) REFERENCES risk_alerts(alert_id)
    )
    """)

    # 11. Data Sources Registry (Operational Intelligence Module 3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data_sources_registry (
        source_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        source_type TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        is_enabled INTEGER DEFAULT 1,
        supported_variables TEXT NOT NULL,
        update_frequency TEXT NOT NULL,
        attribution TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        last_sync TEXT,
        latency_ms INTEGER DEFAULT 45,
        failures_count INTEGER DEFAULT 0,
        notes TEXT
    )
    """)

    # 12. Operational Settings & Thresholds (Module 3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operational_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        updated_at TEXT NOT NULL
    )
    """)

    # 13. Operational Audit Log (Module 2 & 3 Traceability)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operational_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        target TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        performed_by TEXT DEFAULT 'system_operator',
        timestamp TEXT NOT NULL,
        notes TEXT
    )
    """)

    # Seed Standard Meteorological Data Sources if not already present
    default_sources = [
        (
            "open_meteo",
            "Open-Meteo Operational NWP",
            "primary_api",
            "https://api.open-meteo.com/v1/forecast",
            1,
            json.dumps(["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "rain", "surface_pressure", "wind_speed_10m", "wind_gusts_10m", "cloud_cover"]),
            "Hourly assimilation (~9km ECMWF IFS / GFS regional)",
            "Open-Meteo (CC BY 4.0) & ECMWF IFS",
            "ACTIVE",
            datetime.now().isoformat(),
            62,
            0,
            "Primary NWP operational weather forecast ingestion adapter"
        ),
        (
            "imd_rmc",
            "India Meteorological Department (IMD) / RMC Chennai",
            "authoritative_warning",
            "https://mausam.imd.gov.in/chennai/",
            1,
            json.dumps(["cyclone_bulletins", "district_nowcasts", "color_coded_warnings", "monsoon_departure"]),
            "Synoptic 6-hourly & Special Alerts",
            "IMD, Ministry of Earth Sciences, Govt. of India",
            "ACTIVE",
            datetime.now().isoformat(),
            48,
            0,
            "Authoritative warning adapter for regional synoptic bulletins and alerts"
        ),
        (
            "nasa_power",
            "NASA POWER Agro-Climatology",
            "historical_enrichment",
            "https://power.larc.nasa.gov/api/temporal/daily/point",
            1,
            json.dumps(["allsky_sfc_sw_dwn", "t2m", "rh2m", "prectotcorr", "solar_radiation"]),
            "Daily historical & agro-meteorological updates",
            "NASA Langley Research Center POWER Project",
            "ACTIVE",
            datetime.now().isoformat(),
            120,
            0,
            "Agro-climatological and solar irradiance enrichment adapter"
        ),
        (
            "copernicus_cds",
            "Copernicus Climate Data Store (ERA5)",
            "reanalysis_baseline",
            "https://cds.climate.copernicus.eu/",
            1,
            json.dumps(["era5_temperature", "era5_precipitation", "climatological_30yr_normals"]),
            "Decadal reanalysis baseline (1991-2020 normals)",
            "ECMWF / Copernicus Climate Change Service",
            "ACTIVE",
            datetime.now().isoformat(),
            85,
            0,
            "Reanalysis baseline and long-period departure evaluation"
        ),
        (
            "huggingface",
            "Hugging Face Climate Foundation Benchmark",
            "foundation_benchmark",
            "https://huggingface.co/google/timesfm-1.0-200m",
            1,
            json.dumps(["timesfm_embeddings", "zero_shot_temperature_forecast", "rolling_eval_weights"]),
            "Model release evaluation cycles",
            "Google Research & Hugging Face Hub",
            "ACTIVE",
            datetime.now().isoformat(),
            140,
            0,
            "Pretrained zero-shot foundation model benchmarking adapter"
        )
    ]

    for src in default_sources:
        cursor.execute("""
        INSERT OR IGNORE INTO data_sources_registry (
            source_id, name, source_type, endpoint, is_enabled,
            supported_variables, update_frequency, attribution,
            status, last_sync, latency_ms, failures_count, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, src)

    # Seed Default Operational Settings if not present
    default_settings = [
        ("default_forecast_horizon_hours", "24", "forecast", "Default horizon for operational guidance and sector matrix evaluation"),
        ("rain_accumulation_window_hours", "24", "indicators", "Time window for cumulative rainfall risk calculation"),
        ("apparent_temp_formula", "rothfusz", "indicators", "Apparent temperature formula: rothfusz or steadman"),
        ("cache_ttl_live_seconds", "900", "storage", "In-memory & SQLite cache TTL for live weather telemetry"),
        ("cache_ttl_forecast_seconds", "3600", "storage", "Cache TTL for multi-day NWP numerical forecasts"),
        ("stale_data_threshold_minutes", "60", "observability", "Elapsed minutes after which telemetry is flagged as stale")
    ]
    for s_key, s_val, s_cat, s_desc in default_settings:
        cursor.execute("""
        INSERT OR IGNORE INTO operational_settings (
            setting_key, setting_value, category, description, updated_at
        ) VALUES (?, ?, ?, ?, ?)
        """, (s_key, s_val, s_cat, s_desc, datetime.now().isoformat()))

    for col_def in [
        ("timestamp_utc", "TEXT"),
        ("dew_point_2m", "REAL"),
        ("cloud_cover", "REAL")
    ]:
        try:
            cursor.execute(f"ALTER TABLE weather_records ADD COLUMN {col_def[0]} {col_def[1]}")
        except sqlite3.OperationalError:
            pass # column already exists

    # Seed Locations
    for dist_id, dist_info in TAMIL_NADU_DISTRICTS.items():
        loc_id = f"DIST_{dist_id.upper()}"
        for core in CORE_MONITORING_LOCATIONS:
            if core["district_id"] == dist_id:
                loc_id = core["location_id"]
                break

        cursor.execute("""
        INSERT OR REPLACE INTO locations (
            location_id, district_id, name, tamil_name, region,
            latitude, longitude, elevation_m, is_coastal, is_hill,
            normal_annual_rainfall_mm, nem_normal_mm, swm_normal_mm,
            primary_crops, critical_reservoirs, agriculture_impact
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            loc_id,
            dist_id,
            dist_info["name"],
            dist_info.get("tamil_name", ""),
            dist_info.get("region", "Interior Plains"),
            dist_info["lat"],
            dist_info["lon"],
            dist_info["elevation_m"],
            1 if dist_info["is_coastal"] else 0,
            1 if dist_info["elevation_m"] > 1000 else 0,
            dist_info.get("normal_annual_rainfall_mm", 950.0),
            dist_info.get("nem_normal_mm", 450.0),
            dist_info.get("swm_normal_mm", 320.0),
            json.dumps(dist_info.get("primary_crops", []), ensure_ascii=False),
            json.dumps(dist_info.get("critical_reservoirs", []), ensure_ascii=False),
            dist_info.get("agriculture_impact", "")
        ))

    conn.commit()
    conn.close()


def log_ingestion_job(
    job_id: str,
    source: str,
    location_id: Optional[str],
    status: str,
    duration_ms: int,
    records_count: int,
    error_category: Optional[str] = None,
    error_message: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ingestion_logs (
            job_id, source, location_id, status, duration_ms,
            records_count, error_category, error_message, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id, source, location_id, status, duration_ms,
        records_count, error_category, error_message, datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_cached_item(cache_key: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    cursor.execute("""
        SELECT data_json, updated_at FROM live_cache 
        WHERE cache_key = ? AND expires_at > ?
    """, (cache_key, now_iso))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = json.loads(row["data_json"])
        data["cached_at"] = row["updated_at"]
        return data
    return None


def set_cached_item(cache_key: str, data: Dict[str, Any], ttl_seconds: int = 1800):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()
    now_iso = now.isoformat()
    expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat()
    data_json = json.dumps(data)
    cursor.execute("""
        INSERT OR REPLACE INTO live_cache (cache_key, data_json, updated_at, expires_at)
        VALUES (?, ?, ?, ?)
    """, (cache_key, data_json, now_iso, expires_at))
    conn.commit()
    conn.close()


def insert_weather_records_batch(records: List[Dict[str, Any]]) -> int:
    """
    Idempotent insert into weather_records.
    Uses INSERT OR IGNORE so repeat ingestion does NOT create duplicates!
    """
    if not records:
        return 0
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR IGNORE INTO weather_records (
            location_id, timestamp, timestamp_utc, temperature_2m, relative_humidity_2m,
            dew_point_2m, precipitation_mm, wind_speed_10m, wind_direction_10m,
            pressure_msl, cloud_cover, source_type, lead_time_hours, forecast_init_time,
            fetched_at, quality_flag
        ) VALUES (
            :location_id, :timestamp, :timestamp_utc, :temperature_2m, :relative_humidity_2m,
            :dew_point_2m, :precipitation_mm, :wind_speed_10m, :wind_direction_10m,
            :pressure_msl, :cloud_cover, :source_type, :lead_time_hours, :forecast_init_time,
            :fetched_at, :quality_flag
        )
    """, records)
    inserted = cursor.rowcount
    conn.commit()
    conn.close()
    return inserted


def log_pipeline_run(
    run_id: str,
    run_type: str,
    start_time: str,
    end_time: str,
    status: str,
    locations_count: int,
    records_ingested: int,
    records_quarantined: int,
    duration_ms: int,
    completeness_pct: float,
    freshness_minutes: float,
    report_path: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO pipeline_runs (
            run_id, run_type, start_time, end_time, status,
            locations_count, records_ingested, records_quarantined,
            duration_ms, completeness_pct, freshness_minutes, report_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, run_type, start_time, end_time, status,
        locations_count, records_ingested, records_quarantined,
        duration_ms, completeness_pct, freshness_minutes, report_path
    ))
    conn.commit()
    conn.close()


def save_climate_report(report_dict: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO climate_reports (
            report_id, title, district_id, start_year, end_year,
            season, variable, pdf_path, csv_path, summary_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_dict["report_id"],
        report_dict["title"],
        report_dict["district_id"],
        report_dict["start_year"],
        report_dict["end_year"],
        report_dict["season"],
        report_dict["variable"],
        report_dict.get("pdf_path"),
        report_dict.get("csv_path"),
        json.dumps(report_dict.get("summary", {})),
        report_dict.get("created_at", datetime.now().isoformat())
    ))
    conn.commit()
    conn.close()


def get_climate_report(report_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM climate_reports WHERE report_id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        r = dict(row)
        if r.get("summary_json"):
            try:
                r["summary"] = json.loads(r["summary_json"])
            except Exception:
                r["summary"] = {}
        return r
    return None


def save_ml_experiment(exp_dict: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO ml_experiments (
            experiment_id, name, target_variable, horizon_hours,
            models_evaluated, best_model, train_start, train_end,
            val_start, val_end, test_start, test_end,
            metrics_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        exp_dict["experiment_id"],
        exp_dict["name"],
        exp_dict["target_variable"],
        exp_dict.get("horizon_hours", 24),
        json.dumps(exp_dict.get("models_evaluated", [])),
        exp_dict.get("best_model", "lightgbm"),
        exp_dict.get("train_start"),
        exp_dict.get("train_end"),
        exp_dict.get("val_start"),
        exp_dict.get("val_end"),
        exp_dict.get("test_start"),
        exp_dict.get("test_end"),
        json.dumps(exp_dict.get("metrics", {})),
        exp_dict.get("created_at", datetime.now().isoformat())
    ))
    conn.commit()
    conn.close()


def get_ml_experiments(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ml_experiments ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for row in rows:
        r = dict(row)
        if r.get("models_evaluated"):
            try:
                r["models_evaluated"] = json.loads(r["models_evaluated"])
            except Exception:
                pass
        if r.get("metrics_json"):
            try:
                r["metrics"] = json.loads(r["metrics_json"])
            except Exception:
                pass
        results.append(r)
    return results


def save_ml_model_record(model_dict: Dict[str, Any]):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO ml_model_registry (
            model_id, name, model_type, target_variable, horizon_hours,
            artifact_path, val_mae, val_rmse, val_f1,
            test_mae, test_rmse, test_f1, is_active_best,
            hyperparameters_json, registered_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        model_dict["model_id"],
        model_dict["name"],
        model_dict["model_type"],
        model_dict["target_variable"],
        model_dict.get("horizon_hours", 24),
        model_dict.get("artifact_path"),
        model_dict.get("val_mae"),
        model_dict.get("val_rmse"),
        model_dict.get("val_f1"),
        model_dict.get("test_mae"),
        model_dict.get("test_rmse"),
        model_dict.get("test_f1"),
        1 if model_dict.get("is_active_best") else 0,
        json.dumps(model_dict.get("hyperparameters", {})),
        model_dict.get("registered_at", datetime.now().isoformat())
    ))
    conn.commit()
    conn.close()


def get_ml_models() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ml_model_registry ORDER BY registered_at DESC")
    rows = cursor.fetchall()
    conn.close()
    results = []
    for row in rows:
        r = dict(row)
        if r.get("hyperparameters_json"):
            try:
                r["hyperparameters"] = json.loads(r["hyperparameters_json"])
            except Exception:
                r["hyperparameters"] = {}
        results.append(r)
    return results


if __name__ == "__main__":
    init_db()
    print("Database schema successfully verified at", DB_PATH)
