from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient

from app.api.routes.historical import get_historical_service
from app.main import app
from app.services.historical import HistoricalService


class UnusedClient:
    pass


@pytest.fixture
def test_historical_service(database, tmp_path):
    from app.services.locations import LocationService

    catalogue = tmp_path / "locations.json"
    catalogue.write_text(
        '[{"id":"test-loc","name":"Test City","state":"Test State","type":"city","latitude":25.0,"longitude":80.0,"timezone":"Asia/Kolkata"}]'
    )
    locations = LocationService(catalogue)
    return HistoricalService(database, tmp_path, locations, UnusedClient())


def test_heat_patterns_calculation(test_historical_service):
    # Create dataset with 30 days of data in May (summer)
    start = date(2024, 5, 1)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(30)]
    # Temperatures: 10 days of 36°C, 10 days of 41°C, 10 days of 46°C
    temperatures = [36.0] * 10 + [41.0] * 10 + [46.0] * 10
    daily = {
        "time": dates,
        "temperature_2m_max": temperatures,
        "temperature_2m_mean": [t - 5.0 for t in temperatures],
    }
    job = {"start_date": dates[0], "end_date": dates[-1]}
    dataset_id = test_historical_service._write_dataset(
        test_historical_service.locations.get("test-loc"),
        job,
        daily,
        {"temperature_2m_max": "°C", "temperature_2m_mean": "°C"},
    )

    result = test_historical_service.heat_patterns(dataset_id, threshold_celsius=40.0)

    assert result["dataset_id"] == dataset_id
    assert result["total_days_analyzed"] == 30
    assert result["days_above_35c"] == 30
    assert result["days_above_40c"] == 20
    assert result["days_above_45c"] == 10
    assert result["days_above_threshold"] == 20
    assert result["max_consecutive_hot_days"] == 20
    assert result["peak_temperature"]["temperature"] == 46.0
    assert result["peak_temperature"]["date"] == dates[20]
    assert result["summer_season_summary"]["days_with_data"] == 30
    assert result["summer_season_summary"]["hot_days_count"] == 20
    assert "2024-05" in result["monthly_hot_days"]
    assert "ERA5 reanalysis" in result["source_note"]


def test_heat_patterns_endpoint(test_historical_service):
    start = date(2024, 6, 1)
    dates = [(start + timedelta(days=i)).isoformat() for i in range(10)]
    temperatures = [42.0] * 10
    daily = {"time": dates, "temperature_2m_max": temperatures}
    job = {"start_date": dates[0], "end_date": dates[-1]}
    dataset_id = test_historical_service._write_dataset(
        test_historical_service.locations.get("test-loc"),
        job,
        daily,
        {"temperature_2m_max": "°C"},
    )

    app.dependency_overrides[get_historical_service] = lambda: test_historical_service
    try:
        response = TestClient(app).get(
            "/api/v1/historical/heat-patterns",
            params={"dataset_id": dataset_id, "threshold_celsius": 40.0},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["total_days_analyzed"] == 10
    assert data["days_above_40c"] == 10
    assert data["max_consecutive_hot_days"] == 10
