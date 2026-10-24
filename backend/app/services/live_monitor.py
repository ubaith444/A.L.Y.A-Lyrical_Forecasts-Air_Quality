"""Live Location Monitoring Service for A.L.Y.A.

Combines live device coordinates with Numerical Weather Prediction (NWP),
CAMS / Open-Meteo Air Quality, and microclimatic spatial gradient analysis.

Core principles:
- Clearly separate device GPS accuracy (meters) from weather model grid resolution (~10 km).
- Provide movement detection using the Haversine distance formula.
- Analyze surrounding microclimates (+5 km spatial offset) around the user's location.
"""

from datetime import datetime, timezone
import math
from typing import Any
import uuid

# In-memory audit trail for location movement events
LOCATION_MOVEMENT_AUDIT_LOG: list[dict[str, Any]] = []


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 1)


class LiveLocationMonitorService:
    """Evaluates live GPS surroundings, microclimatic gradients, and movement tracking."""

    @classmethod
    def get_nearby_offsets(cls, latitude: float, longitude: float) -> list[dict[str, Any]]:
        """Generates 4 surrounding cardinal sampling points (~5 km offset)

        to evaluate spatial weather gradients (e.g. coastal cooling vs inland heat).
        """
        # ~0.045 degrees is approximately 5 km in latitude and longitude in southern India
        offset_deg = 0.045
        return [
            {
                "label": "Current GPS Fix",
                "direction": "Center",
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "distance_km": 0.0,
            },
            {
                "label": "North Sector (+5 km)",
                "direction": "North",
                "latitude": round(latitude + offset_deg, 4),
                "longitude": round(longitude, 4),
                "distance_km": 5.0,
            },
            {
                "label": "East / Coastal Sector (+5 km)",
                "direction": "East",
                "latitude": round(latitude, 4),
                "longitude": round(longitude + offset_deg, 4),
                "distance_km": 5.0,
            },
            {
                "label": "South Sector (+5 km)",
                "direction": "South",
                "latitude": round(latitude - offset_deg, 4),
                "longitude": round(longitude, 4),
                "distance_km": 5.0,
            },
            {
                "label": "West / Inland Sector (+5 km)",
                "direction": "West",
                "latitude": round(latitude, 4),
                "longitude": round(longitude - offset_deg, 4),
                "distance_km": 5.0,
            },
        ]

    @classmethod
    def log_movement_event(
        cls,
        latitude: float,
        longitude: float,
        accuracy_m: float | None = None,
        previous_lat: float | None = None,
        previous_lon: float | None = None,
        trigger_threshold_m: float = 500.0,
    ) -> dict[str, Any]:
        """Logs a device position update, checks movement threshold, and records audit trail."""
        distance_moved = 0.0
        threshold_exceeded = False

        if previous_lat is not None and previous_lon is not None:
            distance_moved = haversine_distance_m(previous_lat, previous_lon, latitude, longitude)
            if distance_moved >= trigger_threshold_m:
                threshold_exceeded = True

        event_id = str(uuid.uuid4())
        record = {
            "event_id": event_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latitude": round(latitude, 5),
            "longitude": round(longitude, 5),
            "accuracy_m": round(accuracy_m, 1) if accuracy_m is not None else None,
            "distance_moved_m": distance_moved,
            "threshold_m": trigger_threshold_m,
            "refresh_triggered": threshold_exceeded or (previous_lat is None),
        }

        LOCATION_MOVEMENT_AUDIT_LOG.append(record)
        return record

    @classmethod
    def get_movement_history(cls, limit: int = 20) -> list[dict[str, Any]]:
        """Returns recent GPS movement updates."""
        return list(reversed(LOCATION_MOVEMENT_AUDIT_LOG[-limit:]))
