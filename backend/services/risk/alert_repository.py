"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 5: Alert Repository (SQLite Persistence & Lifecycle Audit)

Maintains persistent alert lifecycle:
Active -> Updated -> Resolved

Implements:
1. Strict duplicate alert prevention for ongoing meteorological events.
2. Complete audit trail of previous trigger values and threshold transitions.
3. User acknowledgment recording (acknowledged, acknowledged_at).
4. CSV export of alert history with full audit provenance.
5. Zero PostgreSQL dependency (utilizes embedded SQLite database).
"""

import os
import io
import csv
import json
import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from backend.data.database import DB_PATH, get_db_connection


def init_risk_tables():
    """Initializes SQLite schema for risk alerts and audit trails."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS risk_alerts (
        alert_id TEXT PRIMARY KEY,
        district_id TEXT NOT NULL,
        hazard_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        trigger_value REAL NOT NULL,
        threshold_value REAL NOT NULL,
        unit TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL, -- 'Active', 'Updated', 'Resolved'
        acknowledged INTEGER DEFAULT 0,
        acknowledged_at TEXT,
        previous_value REAL,
        source TEXT NOT NULL,
        summary_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        resolved_at TEXT
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_risk_alerts_query
    ON risk_alerts(district_id, hazard_type, severity, status)
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alert_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id TEXT NOT NULL,
        action TEXT NOT NULL, -- 'CREATED', 'UPDATED', 'ACKNOWLEDGED', 'RESOLVED'
        old_severity TEXT,
        new_severity TEXT,
        old_value REAL,
        new_value REAL,
        timestamp TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (alert_id) REFERENCES risk_alerts(alert_id)
    )
    """)

    conn.commit()
    conn.close()


def save_or_update_alert(alert_data: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Saves or transitions an alert.
    Prevents duplicate alerts for the same ongoing hazard in a district:
    - If active alert exists with different trigger value/severity -> Transitions to 'Updated'
    - If condition normalized to Low -> Transitions to 'Resolved'
    - If new hazard -> Inserts 'Active' alert
    """
    init_risk_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    district_id = alert_data["district_id"].lower()
    hazard_type = alert_data["hazard_type"]
    new_severity = alert_data["severity"]
    new_trigger = float(alert_data["trigger_value"])
    now_iso = datetime.now().isoformat()

    # Look for existing Active or Updated alert
    cursor.execute("""
        SELECT * FROM risk_alerts
        WHERE district_id = ? AND hazard_type = ? AND status IN ('Active', 'Updated')
        ORDER BY updated_at DESC LIMIT 1
    """, (district_id, hazard_type))
    existing = cursor.fetchone()

    if existing:
        ex = dict(existing)
        alert_id = ex["alert_id"]
        old_severity = ex["severity"]
        old_trigger = ex["trigger_value"]

        # Check if resolved (returned to Low)
        if new_severity == "Low":
            cursor.execute("""
                UPDATE risk_alerts
                SET status = 'Resolved',
                    previous_value = ?,
                    trigger_value = ?,
                    updated_at = ?,
                    resolved_at = ?,
                    summary_json = ?
                WHERE alert_id = ?
            """, (old_trigger, new_trigger, now_iso, now_iso, json.dumps(alert_data.get("bilingual_summary", {})), alert_id))

            cursor.execute("""
                INSERT INTO alert_audit_log (alert_id, action, old_severity, new_severity, old_value, new_value, timestamp, notes)
                VALUES (?, 'RESOLVED', ?, 'Low', ?, ?, ?, 'Weather conditions returned below hazard threshold.')
            """, (alert_id, old_severity, old_trigger, new_trigger, now_iso))

            conn.commit()
            conn.close()
            ex["status"] = "Resolved"
            ex["trigger_value"] = new_trigger
            return ex, "RESOLVED"

        # Check if modified / updated
        if old_severity != new_severity or abs(old_trigger - new_trigger) > 0.5:
            cursor.execute("""
                UPDATE risk_alerts
                SET severity = ?,
                    trigger_value = ?,
                    threshold_value = ?,
                    previous_value = ?,
                    reason = ?,
                    status = 'Updated',
                    updated_at = ?,
                    summary_json = ?
                WHERE alert_id = ?
            """, (
                new_severity,
                new_trigger,
                alert_data["threshold_value"],
                old_trigger,
                alert_data["reason"],
                now_iso,
                json.dumps(alert_data.get("bilingual_summary", {})),
                alert_id
            ))

            cursor.execute("""
                INSERT INTO alert_audit_log (alert_id, action, old_severity, new_severity, old_value, new_value, timestamp, notes)
                VALUES (?, 'UPDATED', ?, ?, ?, ?, ?, 'Alert trigger value or severity level updated.')
            """, (alert_id, old_severity, new_severity, old_trigger, new_trigger, now_iso))

            conn.commit()
            conn.close()
            ex["severity"] = new_severity
            ex["trigger_value"] = new_trigger
            ex["status"] = "Updated"
            return ex, "UPDATED"

        # Unchanged active event - prevent duplicate!
        conn.close()
        return ex, "UNCHANGED"

    else:
        # If new condition is Low, do not create an active alert
        if new_severity == "Low":
            conn.close()
            return alert_data, "SKIPPED_LOW"

        # Create brand-new Active alert
        uid = uuid.uuid4().hex[:6].upper()
        alert_id = f"ALT_{district_id.upper()[:3]}_{hazard_type.upper()[:4]}_{datetime.now().strftime('%Y%m%d%H%M')}_{uid}"
        cursor.execute("""
            INSERT OR REPLACE INTO risk_alerts (
                alert_id, district_id, hazard_type, severity, trigger_value,
                threshold_value, unit, reason, status, acknowledged, previous_value,
                source, summary_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', 0, NULL, ?, ?, ?, ?)
        """, (
            alert_id,
            district_id,
            hazard_type,
            new_severity,
            new_trigger,
            alert_data["threshold_value"],
            alert_data["unit"],
            alert_data["reason"],
            alert_data.get("source", "Open-Meteo & IMD Numerical Ensemble"),
            json.dumps(alert_data.get("bilingual_summary", {})),
            now_iso,
            now_iso
        ))

        cursor.execute("""
            INSERT INTO alert_audit_log (alert_id, action, old_severity, new_severity, old_value, new_value, timestamp, notes)
            VALUES (?, 'CREATED', NULL, ?, NULL, ?, ?, 'Initial threshold breach registered.')
        """, (alert_id, new_severity, new_trigger, now_iso))

        conn.commit()
        conn.close()

        alert_data["alert_id"] = alert_id
        alert_data["status"] = "Active"
        alert_data["created_at"] = now_iso
        alert_data["updated_at"] = now_iso
        return alert_data, "CREATED"


def acknowledge_alert(alert_id: str) -> Optional[Dict[str, Any]]:
    """Marks an alert as acknowledged by the operator."""
    init_risk_tables()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()

    cursor.execute("SELECT * FROM risk_alerts WHERE alert_id = ?", (alert_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    cursor.execute("""
        UPDATE risk_alerts
        SET acknowledged = 1, acknowledged_at = ?
        WHERE alert_id = ?
    """, (now_iso, alert_id))

    cursor.execute("""
        INSERT INTO alert_audit_log (alert_id, action, old_severity, new_severity, old_value, new_value, timestamp, notes)
        VALUES (?, 'ACKNOWLEDGED', NULL, NULL, NULL, NULL, ?, 'Alert acknowledged by operator.')
    """, (alert_id, now_iso))

    conn.commit()

    cursor.execute("SELECT * FROM risk_alerts WHERE alert_id = ?", (alert_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return dict(updated_row) if updated_row else None


def get_alerts_list(
    district_id: Optional[str] = None,
    severity: Optional[str] = None,
    hazard_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Queries alerts from SQLite with configurable filters."""
    init_risk_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM risk_alerts WHERE 1=1"
    params = []

    if district_id:
        query += " AND district_id = ?"
        params.append(district_id.lower())
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if hazard_type:
        query += " AND hazard_type = ?"
        params.append(hazard_type)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        if d.get("summary_json"):
            try:
                d["bilingual_summary"] = json.loads(d["summary_json"])
            except Exception:
                d["bilingual_summary"] = {}
        results.append(d)
    return results


def get_alert_by_id(alert_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a single alert by its ID including full audit logs."""
    init_risk_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM risk_alerts WHERE alert_id = ?", (alert_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    alert_dict = dict(row)
    if alert_dict.get("summary_json"):
        try:
            alert_dict["bilingual_summary"] = json.loads(alert_dict["summary_json"])
        except Exception:
            alert_dict["bilingual_summary"] = {}

    # Fetch audit logs
    cursor.execute("SELECT * FROM alert_audit_log WHERE alert_id = ? ORDER BY id ASC", (alert_id,))
    logs = cursor.fetchall()
    alert_dict["audit_history"] = [dict(log) for log in logs]
    conn.close()
    return alert_dict


def export_alerts_to_csv_string(
    district_id: Optional[str] = None,
    hazard_type: Optional[str] = None,
    severity: Optional[str] = None
) -> str:
    """Generates an audit-ready CSV string of alert records."""
    alerts = get_alerts_list(district_id=district_id, severity=severity, hazard_type=hazard_type, limit=500)
    
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        "Alert ID", "District ID", "Hazard Type", "Severity", "Trigger Value",
        "Threshold Value", "Unit", "Reason", "Status", "Acknowledged",
        "Acknowledged At", "Previous Value", "Source", "Created At", "Updated At", "Resolved At"
    ])

    for a in alerts:
        writer.writerow([
            a.get("alert_id"),
            a.get("district_id"),
            a.get("hazard_type"),
            a.get("severity"),
            a.get("trigger_value"),
            a.get("threshold_value"),
            a.get("unit"),
            a.get("reason"),
            a.get("status"),
            "YES" if a.get("acknowledged") else "NO",
            a.get("acknowledged_at") or "",
            a.get("previous_value") or "",
            a.get("source"),
            a.get("created_at"),
            a.get("updated_at"),
            a.get("resolved_at") or ""
        ])

    return output.getvalue()
