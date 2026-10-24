from pathlib import Path

import pytest

from app.core.database import Database
from app.services.cache import ResponseCache


@pytest.fixture
def database(tmp_path: Path) -> Database:
    instance = Database(tmp_path / "alya.db")
    instance.initialize()
    return instance


@pytest.fixture
def cache(database: Database) -> ResponseCache:
    return ResponseCache(database, ttl_seconds=60)
