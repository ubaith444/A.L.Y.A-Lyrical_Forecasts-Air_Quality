import json
from datetime import date, timedelta

import pytest

from app.services.evaluation import EvaluationService
from app.services.historical import HistoricalService
from app.core.errors import ApiError


class UnusedClient:
    pass


def build_service(database, tmp_path, location_service):
    return HistoricalService(database, tmp_path, location_service, UnusedClient())


@pytest.fixture
def location_service(tmp_path):
    from app.services.locations import LocationService

    catalogue = tmp_path / "locations.json"
    catalogue.write_text(
        '[{"id":"test","name":"Test","state":"Test","type":"city","latitude":1,"longitude":1,"timezone":"Asia/Kolkata"}]'
    )
    return LocationService(catalogue)


def test_historical_ingestion_rejects_duplicate_timestamps(
    database, tmp_path, location_service
):
    service = build_service(database, tmp_path, location_service)
    job = {"start_date": "2024-01-01", "end_date": "2024-01-02"}
    daily = {"time": ["2024-01-01", "2024-01-01"], "temperature_2m_mean": [20, 21]}

    with pytest.raises(ValueError, match="duplicate"):
        service._write_dataset(location_service.get("test"), job, daily, {})
    assert not list((tmp_path / "historical").glob("*.csv"))


def test_evaluation_uses_chronological_persistence_baseline(
    database, tmp_path, location_service
):
    service = build_service(database, tmp_path, location_service)
    start = date(2024, 1, 1)
    times = [(start + timedelta(days=index)).isoformat() for index in range(25)]
    daily = {"time": times, "temperature_2m_mean": list(range(25))}
    job = {"start_date": times[0], "end_date": times[-1]}
    dataset_id = service._write_dataset(
        location_service.get("test"), job, daily, {"temperature_2m_mean": "°C"}
    )

    result = EvaluationService(database, service).evaluate_persistence(
        dataset_id, "temperature_2m_mean"
    )

    assert result["status"] == "baseline_only"
    assert result["training_period"]["samples"] == 20
    assert result["test_period"]["samples"] == 5
    assert result["metrics"] == {"mae": 1.0, "rmse": 1.0}


def test_historical_reader_rejects_dataset_file_outside_storage(
    database, tmp_path, location_service
):
    service = build_service(database, tmp_path, location_service)
    outside_file = tmp_path / "outside.csv"
    outside_file.write_text("date,temperature_2m_mean\n2024-01-01,20\n")
    with database.connection() as connection:
        connection.execute(
            """INSERT INTO historical_datasets(
                id, location_id, source, data_kind, file_path, start_date, end_date,
                retrieved_at, row_count, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "unsafe-dataset",
                "test",
                "test",
                "reanalysis",
                str(outside_file),
                "2024-01-01",
                "2024-01-01",
                "2024-01-02T00:00:00+00:00",
                1,
                json.dumps({}),
            ),
        )

    with pytest.raises(ApiError, match="dataset_unavailable"):
        list(service.read_rows("unsafe-dataset"))
