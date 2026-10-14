"""
Tamil Nadu Climate & Forecast Intelligence Platform
Operational Intelligence Module 2: Sector Matrix CSV Export

Generates auditable, structured CSV datasets containing multi-sector assessments,
hazard likelihood, exposure, vulnerability scores, and guidance.
"""

import io
import csv
from typing import List, Dict, Any, Optional
from backend.services.impact.sector_matrix import get_all_districts_sector_matrix


def export_sector_matrix_to_csv_string(
    sector_filter: Optional[str] = None,
    horizon_hours: int = 24
) -> str:
    """
    Serializes 38-district sector matrix assessments to standard RFC 4180 CSV with data provenance.
    """
    records = get_all_districts_sector_matrix(sector_filter=sector_filter, horizon_hours=horizon_hours)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header Row
    writer.writerow([
        "District_ID",
        "District_Name",
        "Tamil_Name",
        "Region",
        "Horizon_Hours",
        "Sector_Key",
        "Sector_Name",
        "Composite_Score",
        "Severity_Level",
        "Hazard_Likelihood",
        "Exposure_Score",
        "Vulnerability_Score",
        "Meteorological_Drivers",
        "Potential_Operational_Impact",
        "Recommended_Guidance",
        "Monitored_Assets",
        "Evaluated_At_UTC"
    ])

    for r in records:
        d_id = r["district_id"]
        d_name = r["district_name"]
        t_name = r["tamil_name"]
        reg = r["region"]
        eval_time = r["evaluated_at"]

        sectors = r.get("sectors", {})
        if sector_filter and sector_filter.lower() in sectors:
            target_sectors = {sector_filter.lower(): sectors[sector_filter.lower()]}
        else:
            target_sectors = sectors

        for s_key, s_data in target_sectors.items():
            writer.writerow([
                d_id,
                d_name,
                t_name,
                reg,
                horizon_hours,
                s_key,
                s_data["sector_name"],
                s_data["composite_score"],
                s_data["severity"],
                s_data["hazard_likelihood"],
                s_data["exposure_score"],
                s_data["vulnerability_score"],
                s_data["meteorological_drivers"],
                s_data["potential_operational_impact"],
                s_data["recommended_guidance"],
                "; ".join(s_data.get("primary_assets_monitored", [])),
                eval_time
            ])

    return output.getvalue()
