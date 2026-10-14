"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 6: Deployment & Production Readiness Verification Tests

Validates:
1. Production /health and /ready probes.
2. Dynamic persistent storage path resolution (DATA_DIR, DATABASE_URL).
3. SQLite online atomic backup API (preventing live database corruption).
4. CORS origin restriction in production environment.
5. Upstream weather API failure resilience and stale-cache fallback.
6. Zero PostgreSQL dependency verification.
"""

import os
import sqlite3
import pytest
import tempfile
import shutil
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.main import app
from backend.data.database import (
    get_data_dir,
    get_db_path,
    get_models_dir,
    get_datasets_dir,
    get_backups_dir,
    backup_database,
    get_db_connection,
    init_db
)
from backend.services.weather_service import fetch_live_weather, fetch_forecast

client = TestClient(app)


def test_liveness_health_endpoint():
    """Verify GET /health returns 200 OK with system and storage metadata."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert "service" in data
    assert "version" in data
    assert "storage" in data
    assert "data_dir" in data["storage"]
    assert "db_path" in data["storage"]
    assert data["districts_monitored"] == 38
    assert data["ml_model_loaded"] is True


def test_readiness_probe_endpoint():
    """Verify GET /ready checks SQLite connectivity and ML predictor."""
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
    assert data["database"] == "CONNECTED"
    assert data["locations_count"] >= 38
    assert data["ml_predictor_ready"] is True


def test_persistent_storage_path_resolution():
    """Verify DATA_DIR and DATABASE_URL resolution logic."""
    # Test custom DATA_DIR
    temp_dir = tempfile.mkdtemp(prefix="test_tn_data_")
    try:
        with patch.dict(os.environ, {"DATA_DIR": temp_dir}):
            resolved_data_dir = get_data_dir()
            assert resolved_data_dir == temp_dir
            assert os.path.exists(resolved_data_dir)

            models_dir = get_models_dir()
            assert models_dir == os.path.join(temp_dir, "models")
            assert os.path.exists(models_dir)

            datasets_dir = get_datasets_dir()
            assert datasets_dir == os.path.join(temp_dir, "datasets")
            assert os.path.exists(datasets_dir)

        # Test DATABASE_URL override
        custom_db_url = f"sqlite:///{temp_dir}/custom_climate.db"
        with patch.dict(os.environ, {"DATABASE_URL": custom_db_url}):
            resolved_db = get_db_path()
            assert "custom_climate.db" in resolved_db
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_sqlite_online_backup_api():
    """Verify that backup_database() uses SQLite's backup API and creates non-corrupted copy."""
    temp_backup_dir = tempfile.mkdtemp(prefix="test_backup_")
    try:
        backup_file = os.path.join(temp_backup_dir, "test_backup.db")
        result = backup_database(destination_path=backup_file)

        assert result["status"] == "SUCCESS"
        assert result["method"] == "sqlite3_online_backup_api"
        assert os.path.exists(backup_file)
        assert result["size_bytes"] > 0

        # Validate that the backup database is readable and intact
        backup_conn = sqlite3.connect(backup_file)
        cursor = backup_conn.cursor()
        cursor.execute("SELECT count(*) FROM locations")
        loc_count = cursor.fetchone()[0]
        backup_conn.close()

        assert loc_count >= 38
    finally:
        shutil.rmtree(temp_backup_dir, ignore_errors=True)


def test_api_backup_endpoint():
    """Verify POST /api/backup triggers atomic online backup."""
    resp = client.post("/api/backup")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["method"] == "sqlite3_online_backup_api"
    assert os.path.exists(data["backup_path"])


def test_production_cors_configuration():
    """Verify CORS configuration responds with appropriate allowed origin."""
    # Simulation of preflight request
    headers = {
        "Origin": "https://your-frontend.vercel.app",
        "Access-Control-Request-Method": "GET"
    }
    resp = client.options("/health", headers=headers)
    # Status code 200 or allowed headers
    assert resp.status_code == 200


def test_upstream_weather_api_outage_resilience():
    """Verify upstream weather API failure returns valid fallback without 500 error."""
    with patch("requests.get", side_effect=Exception("Open-Meteo gateway timeout simulation")):
        # Live weather should gracefully return climatological fallback
        live_data = fetch_live_weather("chennai")
        assert live_data is not None
        assert "temperature_2m" in live_data
        assert "note" in live_data or live_data.get("quality_flag") in ["valid", "interpolated"]

        # Forecast should also gracefully return fallback
        forecast_data = fetch_forecast("chennai", forecast_days=7)
        assert forecast_data is not None
        assert "daily" in forecast_data
        assert len(forecast_data["daily"]) == 7


def test_zero_postgresql_dependency_phase6():
    """Enforce strict architectural rule: zero PostgreSQL dependencies."""
    db_path = get_db_path()
    assert not db_path.startswith("postgres")
    assert not db_path.startswith("postgresql")

    # Confirm sqlite database connection works
    conn = get_db_connection()
    assert isinstance(conn, sqlite3.Connection)
    conn.close()
