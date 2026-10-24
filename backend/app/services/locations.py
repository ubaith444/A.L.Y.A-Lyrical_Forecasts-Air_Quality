import json
from pathlib import Path

from app.core.errors import ApiError


class LocationService:
    def __init__(self, catalogue_path: Path):
        self.catalogue_path = catalogue_path
        self._locations = self._load()

    def _load(self) -> list[dict]:
        try:
            locations = json.loads(self.catalogue_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Location catalogue cannot be loaded") from exc
        ids = set()
        for location in locations:
            if (
                location.get("id") in ids
                or not -90 <= location.get("latitude", 91) <= 90
                or not -180 <= location.get("longitude", 181) <= 180
            ):
                raise RuntimeError(
                    "Location catalogue contains invalid or duplicate records"
                )
            ids.add(location["id"])
        return locations

    def search(
        self,
        query: str | None,
        state: str | None,
        offset: int,
        limit: int,
        loc_type: str | None = None,
    ) -> tuple[list[dict], int]:
        needle = (query or "").strip().casefold()
        state_needle = (state or "").strip().casefold()
        type_needle = (loc_type or "").strip().casefold()
        matches = [
            location
            for location in self._locations
            if (
                not needle
                or needle in location["name"].casefold()
                or needle in location["state"].casefold()
            )
            and (not state_needle or state_needle == location["state"].casefold())
            and (not type_needle or type_needle == location["type"].casefold())
        ]
        return matches[offset : offset + limit], len(matches)

    def states(self) -> list[dict]:
        state_counts: dict[str, dict] = {}
        for location in self._locations:
            s_name = location["state"]
            if s_name not in state_counts:
                state_counts[s_name] = {
                    "state": s_name,
                    "locations_count": 0,
                    "has_state_record": False,
                }
            state_counts[s_name]["locations_count"] += 1
            if location["type"] == "state":
                state_counts[s_name]["has_state_record"] = True
                state_counts[s_name]["latitude"] = location["latitude"]
                state_counts[s_name]["longitude"] = location["longitude"]
        return sorted(state_counts.values(), key=lambda x: x["state"])

    def get(self, location_id: str) -> dict:
        for location in self._locations:
            if location["id"] == location_id:
                return location
        raise ApiError(
            404,
            "location_not_found",
            "The requested location is not in the configured catalogue.",
        )

    def list_all(self) -> list[dict]:
        return list(self._locations)

