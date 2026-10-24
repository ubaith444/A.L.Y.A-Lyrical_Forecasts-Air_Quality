"""Unit tests for the Live Location Monitor Service & Endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.live_monitor import haversine_distance_m, LiveLocationMonitorService

client = TestClient(app)


def test_haversine_distance():
    # Distance between Chennai Central (13.0827, 80.2755) and Marina Beach (13.0475, 80.2824) is ~4 km
    dist = haversine_distance_m(13.0827, 80.2755, 13.0475, 80.2824)
    assert 3500 <= dist <= 4500

    # Same point distance is 0
    assert haversine_distance_m(13.0827, 80.2755, 13.0827, 80.2755) == 0.0


def test_movement_logging_and_threshold():
    # Initial fix
    log1 = LiveLocationMonitorService.log_movement_event(
        latitude=13.0827,
        longitude=80.2707,
        accuracy_m=12.5,
    )
    assert log1["refresh_triggered"] is True

    # Move 100m (below 500m threshold)
    log2 = LiveLocationMonitorService.log_movement_event(
        latitude=13.0835,
        longitude=80.2710,
        previous_lat=13.0827,
        previous_lon=80.2707,
        trigger_threshold_m=500.0,
    )
    assert log2["distance_moved_m"] < 500.0
    assert log2["refresh_triggered"] is False

    # Move 1.5 km (above 500m threshold)
    log3 = LiveLocationMonitorService.log_movement_event(
        latitude=13.0950,
        longitude=80.2800,
        previous_lat=13.0827,
        previous_lon=80.2707,
        trigger_threshold_m=500.0,
    )
    assert log3["distance_moved_m"] > 500.0
    assert log3["refresh_triggered"] is True


def test_api_live_monitor_dossier():
    res = client.get("/api/v1/live-monitor/dossier?latitude=13.0827&longitude=80.2707&accuracy_m=15.0")
    assert res.status_code == 200
    data = res.json()
    assert "device_location" in data
    assert data["device_location"]["accuracy_m"] == 15.0
    assert "weather" in data
    assert "air_quality" in data
    assert "nearby_microclimates" in data
    assert len(data["nearby_microclimates"]) >= 5
    assert "provenance_and_transparency" in data


def test_api_log_movement():
    res = client.post("/api/v1/live-monitor/log-movement", json={
        "latitude": 13.0827,
        "longitude": 80.2707,
        "accuracy_m": 10.0,
        "previous_lat": 13.0700,
        "previous_lon": 80.2600,
        "threshold_m": 500.0,
    })
    assert res.status_code == 200
    data = res.json()
    assert "distance_moved_m" in data
    assert data["refresh_triggered"] is True
