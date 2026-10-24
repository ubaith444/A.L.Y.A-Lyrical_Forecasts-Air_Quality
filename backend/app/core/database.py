import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Database:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    location_id TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    error_message TEXT,
                    dataset_id TEXT
                );
                CREATE TABLE IF NOT EXISTS historical_datasets (
                    id TEXT PRIMARY KEY,
                    location_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    data_kind TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_datasets_location_dates ON historical_datasets(location_id, start_date, end_date);
                CREATE TABLE IF NOT EXISTS model_evaluations (
                    id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    target_variable TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    evaluation_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS trained_models (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    location_id TEXT NOT NULL,
                    target_variable TEXT NOT NULL,
                    horizon_hours INTEGER NOT NULL,
                    algorithm TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    train_rows INTEGER NOT NULL,
                    test_rows INTEGER NOT NULL,
                    metrics_json TEXT NOT NULL,
                    baseline_metrics_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)
