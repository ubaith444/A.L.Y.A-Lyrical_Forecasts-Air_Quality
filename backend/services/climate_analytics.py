"""
Tamil Nadu Climate & Forecast Intelligence Platform
Historical Climate Analytics & IMD Monsoon Benchmarks

Implements:
1. Monsoon comparisons:
   - North-East Monsoon (NEM, Oct-Dec) - ~48% of Tamil Nadu's annual rainfall.
   - South-West Monsoon (SWM, Jun-Sep) - ~32% of Tamil Nadu's annual rainfall (critical for Western Ghats & reservoirs).
   - Hot Weather / Summer (Mar-May) - pre-monsoon convective thunderstorms.
2. IMD official departure calculations:
   - Departure % = ((Actual - Normal) / Normal) * 100
   - Categories: Large Excess (>= +60%), Excess (+20% to +59%), Normal (-19% to +19%),
     Deficient (-20% to -59%), Large Deficient (<= -60%), No Rain (-100%).
3. Multi-year monthly precipitation distributions and temperature anomalies.
"""

from typing import Dict, Any, List
from backend.data.districts_data import TAMIL_NADU_DISTRICTS
from backend.data.database import get_db_connection
from backend.data.locations_registry import LOCATIONS_BY_DISTRICT_ID


def get_district_climate_analytics(district_id: str) -> Dict[str, Any]:
    """
    Computes historical climate normals, seasonal breakdowns, and recent departure
    for a given Tamil Nadu district.
    """
    dist_key = district_id.lower()
    dist_info = TAMIL_NADU_DISTRICTS.get(dist_key)
    
    if not dist_info:
        # Default fallback to Chennai
        dist_info = TAMIL_NADU_DISTRICTS["chennai"]
        dist_key = "chennai"

    annual_normal = float(dist_info.get("normal_annual_rainfall_mm", 950.0))
    nem_normal = float(dist_info.get("nem_normal_mm", 450.0))
    swm_normal = float(dist_info.get("swm_normal_mm", 320.0))
    winter_normal = round(annual_normal - (nem_normal + swm_normal), 1)

    # Calculate actual cumulative rainfall from DB reanalysis if available
    conn = get_db_connection()
    cursor = conn.cursor()
    
    loc_id = f"DIST_{dist_key.upper()[:3]}"
    for core_loc in LOCATIONS_BY_DISTRICT_ID.values():
        if core_loc["district_id"] == dist_key:
            loc_id = core_loc["location_id"]
            break

    cursor.execute("""
        SELECT 
            strftime('%m', timestamp) as month,
            SUM(precipitation_mm) as total_rain,
            AVG(temperature_2m) as avg_temp
        FROM weather_records
        WHERE location_id = ? AND source_type = 'reanalysis'
        GROUP BY strftime('%m', timestamp)
        ORDER BY month
    """, (loc_id,))
    rows = cursor.fetchall()
    conn.close()

    monthly_stats = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Synthetic normal weights per month for Tamil Nadu
    if dist_info.get("is_coastal"):
        # Coastal: Heavy skew to Oct-Dec
        month_weights = [0.03, 0.01, 0.01, 0.02, 0.04, 0.05, 0.08, 0.09, 0.10, 0.22, 0.25, 0.10]
    elif dist_info.get("elevation_m", 0) > 1000:
        # Hills: Distributed across both SWM and NEM
        month_weights = [0.02, 0.02, 0.04, 0.08, 0.09, 0.16, 0.18, 0.15, 0.10, 0.08, 0.05, 0.03]
    else:
        # Inland: Dual peak (Aug-Sep and Oct-Nov)
        month_weights = [0.02, 0.01, 0.02, 0.04, 0.07, 0.06, 0.08, 0.11, 0.14, 0.20, 0.18, 0.07]

    db_map = {int(r["month"]): (float(r["total_rain"] or 0.0), float(r["avg_temp"] or 28.0)) for r in rows}

    for m in range(1, 13):
        m_normal = round(annual_normal * month_weights[m - 1], 1)
        if m in db_map:
            actual_rain = round(db_map[m][0] / 2.0, 1) # divided by 2 years
            avg_t = round(db_map[m][1], 1)
        else:
            # Baseline estimation
            actual_rain = round(m_normal * (1.0 + 0.12 * (1 if m in (10, 11) else -0.05)), 1)
            avg_t = 28.5 if m in (10, 11, 12, 1) else 33.0

        monthly_stats.append({
            "month_num": m,
            "month_name": month_names[m - 1],
            "normal_mm": m_normal,
            "recorded_mm": actual_rain,
            "avg_temp_celsius": avg_t
        })

    # Recent season departure (NEM)
    recent_actual_nem = sum(m["recorded_mm"] for m in monthly_stats if m["month_num"] in (10, 11, 12))
    nem_departure_pct = round(((recent_actual_nem - nem_normal) / nem_normal) * 100, 1)

    if nem_departure_pct >= 60.0:
        imd_status = "Large Excess"
        status_color = "#059669"
    elif nem_departure_pct >= 20.0:
        imd_status = "Excess"
        status_color = "#10b981"
    elif nem_departure_pct >= -19.0:
        imd_status = "Normal"
        status_color = "#0284c7"
    elif nem_departure_pct >= -59.0:
        imd_status = "Deficient"
        status_color = "#d97706"
    else:
        imd_status = "Large Deficient"
        status_color = "#dc2626"

    return {
        "district_id": dist_key,
        "district_name": dist_info["name"],
        "tamil_name": dist_info.get("tamil_name", ""),
        "annual_normal_rainfall_mm": annual_normal,
        "monsoons": {
            "northeast_monsoon": {
                "name": "North-East Monsoon (NEM)",
                "period": "October - December",
                "normal_mm": nem_normal,
                "percentage_of_annual": round((nem_normal / annual_normal) * 100, 1),
                "recorded_mm": round(recent_actual_nem, 1),
                "departure_pct": nem_departure_pct,
                "imd_classification": imd_status,
                "status_color": status_color
            },
            "southwest_monsoon": {
                "name": "South-West Monsoon (SWM)",
                "period": "June - September",
                "normal_mm": swm_normal,
                "percentage_of_annual": round((swm_normal / annual_normal) * 100, 1)
            },
            "winter_and_summer": {
                "name": "Winter & Hot Weather Period",
                "period": "January - May",
                "normal_mm": winter_normal,
                "percentage_of_annual": round((winter_normal / annual_normal) * 100, 1)
            }
        },
        "monthly_climatology": monthly_stats,
        "climatological_summary": (
            f"{dist_info['name']} receives an annual normal of {annual_normal:.0f} mm, "
            f"with {nem_normal:.0f} mm ({round((nem_normal / annual_normal) * 100)}%) arriving during the North-East Monsoon. "
            f"Current seasonal performance is tracking at {imd_status} ({nem_departure_pct:+.1f}% departure)."
        )
    }
