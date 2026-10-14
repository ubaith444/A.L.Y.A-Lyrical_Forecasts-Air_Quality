"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 5: Alert Lifecycle Management Service

Orchestrates:
1. Continuous weather risk assessment across Tamil Nadu's 38 districts.
2. Alert lifecycle state transitions: Active -> Updated -> Resolved.
3. Strict deduplication of ongoing events.
4. User acknowledgment and operator audit trails.
5. Searchable alert history querying and CSV export.
"""

from typing import Dict, Any, List, Optional
from backend.data.districts_data import TAMIL_NADU_DISTRICTS
from backend.services.weather_service import fetch_live_weather, fetch_forecast
from backend.services.risk.risk_engine import evaluate_district_weather_risk
from backend.services.risk.alert_repository import (
    save_or_update_alert,
    acknowledge_alert,
    get_alerts_list,
    get_alert_by_id,
    export_alerts_to_csv_string
)


def evaluate_and_sync_district_alerts(
    district_id: str,
    live_data: Optional[Dict[str, Any]] = None,
    forecast_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Evaluates weather risk for a district and syncs any active/resolved alerts with SQLite.
    """
    if not live_data:
        try:
            live_data = fetch_live_weather(district_id)
        except Exception:
            live_data = {}

    if not forecast_data:
        try:
            forecast_data = fetch_forecast(district_id, forecast_days=3)
        except Exception:
            forecast_data = {}

    assessment = evaluate_district_weather_risk(
        district_id=district_id,
        live_data=live_data,
        forecast_data=forecast_data
    )

    # Sync each hazard with the alert repository
    persisted_alerts = []
    for h in assessment["hazards"]:
        alert_payload = {
            "district_id": district_id.lower(),
            "hazard_type": h["hazard_type"],
            "severity": h["severity"],
            "trigger_value": h["trigger_value"],
            "threshold_value": h["threshold_value"],
            "unit": h["unit"],
            "reason": h["reason"],
            "source": assessment["source"],
            "bilingual_summary": h.get("bilingual_summary", {})
        }
        res, action = save_or_update_alert(alert_payload)
        if action in ["CREATED", "UPDATED", "RESOLVED"]:
            persisted_alerts.append(res)

    assessment["synced_alerts"] = persisted_alerts
    return assessment


def evaluate_statewide_risk_overview() -> Dict[str, Any]:
    """
    Evaluates risk across all 38 Tamil Nadu districts, returns active alert counts,
    severity distributions, and top risk hotspots.
    """
    active_alerts = get_alerts_list(status="Active", limit=200)
    updated_alerts = get_alerts_list(status="Updated", limit=200)
    resolved_alerts = get_alerts_list(status="Resolved", limit=100)

    all_current = active_alerts + updated_alerts

    # Distribution by Severity
    severity_dist = {"Low": 0, "Moderate": 0, "High": 0, "Severe": 0}
    hazard_dist = {"rainfall": 0, "heat": 0, "wind": 0, "dry_spell": 0}
    districts_with_alerts = set()

    for a in all_current:
        sev = a.get("severity", "Low")
        if sev in severity_dist:
            severity_dist[sev] += 1
        haz = a.get("hazard_type", "rainfall")
        if haz in hazard_dist:
            hazard_dist[haz] += 1
        districts_with_alerts.add(a.get("district_id"))

    # Determine Low count for remaining districts
    total_districts = len(TAMIL_NADU_DISTRICTS)
    severity_dist["Low"] = max(0, total_districts - len(districts_with_alerts))

    # Top High-Risk Districts
    high_risk_districts = []
    for a in all_current:
        if a.get("severity") in ["Severe", "High"]:
            d_info = TAMIL_NADU_DISTRICTS.get(a["district_id"], {})
            high_risk_districts.append({
                "district_id": a["district_id"],
                "district_name": d_info.get("name", a["district_id"].capitalize()),
                "hazard_type": a["hazard_type"],
                "severity": a["severity"],
                "trigger_value": a["trigger_value"],
                "unit": a["unit"],
                "reason": a["reason"],
                "alert_id": a["alert_id"],
                "acknowledged": bool(a.get("acknowledged"))
            })

    return {
        "status": "OPERATIONAL",
        "total_districts_monitored": total_districts,
        "active_alerts_count": len(all_current),
        "resolved_alerts_count": len(resolved_alerts),
        "severity_distribution": severity_dist,
        "hazard_distribution": hazard_dist,
        "high_risk_hotspots": high_risk_districts,
        "recent_alerts": all_current[:10],
        "disclaimer": (
            "Application-calculated risk ratings are based on automated algorithms and local thresholds. "
            "They do not replace official warnings issued by the India Meteorological Department (IMD)."
        )
    }


from concurrent.futures import ThreadPoolExecutor

_statewide_cache = {"data": None, "timestamp": 0}

def get_all_district_risk_summaries() -> List[Dict[str, Any]]:
    """Evaluates live risk status for all 38 districts with concurrent execution and caching."""
    import time
    now_ts = time.time()
    if _statewide_cache["data"] and (now_ts - _statewide_cache["timestamp"] < 180):
        return _statewide_cache["data"]

    def _eval(d_id, d_meta):
        assessment = evaluate_and_sync_district_alerts(d_id)
        return {
            "district_id": d_id,
            "district_name": d_meta["name"],
            "region": "Western Ghats" if d_meta["elevation_m"] > 1000 else ("Coastal Corridor" if d_meta["is_coastal"] else "Interior Plains"),
            "composite_severity": assessment["composite_severity"],
            "compound_risk_detected": assessment["compound_risk"]["detected"],
            "compound_description": assessment["compound_risk"]["description"],
            "hazards": assessment["hazards"]
        }

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_eval, d_id, d_meta) for d_id, d_meta in TAMIL_NADU_DISTRICTS.items()]
        results = [f.result() for f in futures]

    _statewide_cache["data"] = results
    _statewide_cache["timestamp"] = now_ts
    return results


def get_single_district_bilingual_summary(district_id: str) -> Dict[str, Any]:
    """Generates detailed bilingual English and Tamil summary for a district."""
    assessment = evaluate_and_sync_district_alerts(district_id)
    return {
        "district_id": assessment["district_id"],
        "district_name": assessment["district_name"],
        "composite_severity": assessment["composite_severity"],
        "compound_risk": assessment["compound_risk"],
        "bilingual_hazards": [h.get("bilingual_summary") for h in assessment["hazards"]],
        "evaluated_at": assessment["evaluated_at"],
        "disclaimer": assessment["disclaimer"]
    }
