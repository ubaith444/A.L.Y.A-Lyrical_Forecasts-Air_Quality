import asyncio
import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, Awaitable, Callable

from app.core.database import Database


class ResponseCache:
    def __init__(self, database: Database, ttl_seconds: int):
        self.database = database
        self.ttl_seconds = ttl_seconds
        self._locks: dict[str, asyncio.Lock] = {}

    async def get_or_fetch(
        self,
        namespace: str,
        params: dict[str, Any],
        fetch: Callable[[], Awaitable[dict[str, Any]]],
    ) -> tuple[dict[str, Any], bool, datetime]:
        key = sha256(
            f"{namespace}:{json.dumps(params, sort_keys=True, default=str)}".encode()
        ).hexdigest()
        cached = self._get(key)
        if cached is not None:
            value, retrieved_at = cached
            return value, True, retrieved_at
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self._get(key)
            if cached is not None:
                value, retrieved_at = cached
                return value, True, retrieved_at
            value = await fetch()
            retrieved_at = self._store(key, value)
            return value, False, retrieved_at

    def _get(self, key: str) -> tuple[dict[str, Any], datetime] | None:
        now = datetime.now(UTC)
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT payload, expires_at, created_at FROM cache_entries WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if row is None:
                return None
            try:
                expires_at = datetime.fromisoformat(row["expires_at"])
                payload = json.loads(row["payload"])
                created_at = datetime.fromisoformat(row["created_at"])
                if (
                    not isinstance(payload, dict)
                    or expires_at.tzinfo is None
                    or created_at.tzinfo is None
                ):
                    raise ValueError("Cache entry has an invalid shape or timestamp")
            except (TypeError, ValueError, json.JSONDecodeError):
                connection.execute(
                    "DELETE FROM cache_entries WHERE cache_key = ?", (key,)
                )
                return None
            if expires_at <= now:
                connection.execute(
                    "DELETE FROM cache_entries WHERE cache_key = ?", (key,)
                )
                return None
            return payload, created_at

    def _store(self, key: str, value: dict[str, Any]) -> datetime:
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(seconds=self.ttl_seconds)
        with self.database.connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO cache_entries(cache_key, payload, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (
                    key,
                    json.dumps(value),
                    expires_at.isoformat(),
                    created_at.isoformat(),
                ),
            )
        return created_at
