import asyncio
from datetime import UTC, datetime

import pytest

from app.services.cache import ResponseCache


@pytest.mark.asyncio
async def test_cache_deduplicates_concurrent_fetches(cache: ResponseCache):
    calls = 0

    async def fetch():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        return {"value": 42}

    results = await asyncio.gather(
        *(cache.get_or_fetch("weather", {"latitude": 1}, fetch) for _ in range(5))
    )

    assert calls == 1
    assert [cached for _, cached, _ in results].count(False) == 1
    assert all(value == {"value": 42} for value, _, _ in results)


@pytest.mark.asyncio
async def test_corrupt_cache_entry_is_deleted_and_refetched(
    cache: ResponseCache, database
):
    with database.connection() as connection:
        connection.execute(
            "INSERT INTO cache_entries(cache_key, payload, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (
                "bad-key",
                "not-json",
                "2999-01-01T00:00:00+00:00",
                datetime.now(UTC).isoformat(),
            ),
        )

    assert cache._get("bad-key") is None
    with database.connection() as connection:
        assert (
            connection.execute(
                "SELECT 1 FROM cache_entries WHERE cache_key = ?", ("bad-key",)
            ).fetchone()
            is None
        )


def test_expired_cache_entry_is_deleted(cache: ResponseCache, database):
    with database.connection() as connection:
        connection.execute(
            "INSERT INTO cache_entries(cache_key, payload, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (
                "expired-key",
                '{"value": 1}',
                "2000-01-01T00:00:00+00:00",
                datetime.now(UTC).isoformat(),
            ),
        )

    assert cache._get("expired-key") is None
    with database.connection() as connection:
        assert (
            connection.execute(
                "SELECT 1 FROM cache_entries WHERE cache_key = ?", ("expired-key",)
            ).fetchone()
            is None
        )


def test_wrong_shape_cache_entry_is_deleted(cache: ResponseCache, database):
    with database.connection() as connection:
        connection.execute(
            "INSERT INTO cache_entries(cache_key, payload, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (
                "wrong-shape",
                "[]",
                "2999-01-01T00:00:00+00:00",
                datetime.now(UTC).isoformat(),
            ),
        )

    assert cache._get("wrong-shape") is None
