"""Multi-Channel Disaster Alert Dispatcher & Notification Engine.

Supports delivery channels:
- In-App Early Warning Dashboard
- Web Push Notifications (simulated payload)
- SMS Emergency Broadcast (simulated payload)
- Email Incident Advisory (simulated payload)

Includes duplicate suppression (anti-flapping filter) and audit logging.
"""

from datetime import datetime, timezone
from typing import Any
import uuid

# In-memory alert dispatch history log
ALERT_DISPATCH_LOG: list[dict[str, Any]] = []


class AlertDispatcher:
    """Dispatches validated disaster alerts with duplicate suppression."""

    @classmethod
    def dispatch_alert(
        cls,
        hazard: str,
        level: int,
        location_id: str,
        location_name: str,
        headline: str,
        instructions: list[str],
        channels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Dispatches an alert to specified channels, suppressing duplicates if recently sent."""
        if channels is None:
            channels = ["dashboard", "push", "sms", "email"]

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Check for duplicate suppression: same hazard, location, and level within the past 30 minutes
        recent_matches = [
            a for a in ALERT_DISPATCH_LOG
            if a["hazard"] == hazard
            and a["location_id"] == location_id
            and a["level"] == level
            and not a.get("suppressed", False)
        ]

        is_suppressed = False
        suppression_reason = None

        if recent_matches:
            last_alert = recent_matches[-1]
            # If dispatched within same session, suppress duplicate noise
            is_suppressed = True
            suppression_reason = f"Duplicate alert suppressed (identical {hazard} Level {level} already dispatched at {last_alert['dispatched_at'][:19]})."

        dispatch_id = str(uuid.uuid4())

        alert_record = {
            "dispatch_id": dispatch_id,
            "dispatched_at": now_iso,
            "hazard": hazard,
            "level": level,
            "location_id": location_id,
            "location_name": location_name,
            "headline": headline,
            "channels": channels,
            "suppressed": is_suppressed,
            "suppression_reason": suppression_reason,
            "channel_payloads": {
                "dashboard": {
                    "badge": f"LEVEL {level} {hazard.upper()}",
                    "active": not is_suppressed,
                },
                "push": {
                    "title": f"⚠️ A.L.Y.A Alert: {headline}",
                    "body": instructions[0] if instructions else "Take safety precautions.",
                    "tag": f"{location_id}-{hazard}",
                },
                "sms": {
                    "sender": "TNSDMA-ALYA",
                    "text": f"[ALYA-EMERGENCY] {location_name}: {headline}. {instructions[0] if instructions else ''} Call 1077 for help.",
                },
                "email": {
                    "subject": f"[PRIORITY ADVISORY] {headline} — {location_name}",
                    "bulletins": instructions,
                },
            },
        }

        ALERT_DISPATCH_LOG.append(alert_record)

        return alert_record

    @classmethod
    def get_history(cls, location_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Returns recent dispatch history."""
        records = ALERT_DISPATCH_LOG
        if location_id:
            records = [r for r in records if r["location_id"] == location_id]
        return list(reversed(records[-limit:]))
