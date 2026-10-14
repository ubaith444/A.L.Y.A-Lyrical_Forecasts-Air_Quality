"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 5: Risk Intelligence Package
"""

from backend.services.risk.thresholds import (
    APPLICATION_THRESHOLDS,
    IMD_WARNING_CRITERIA,
    get_threshold_config
)
from backend.services.risk.risk_engine import (
    compute_heat_index_celsius,
    evaluate_district_weather_risk
)
from backend.services.risk.alert_repository import (
    init_risk_tables,
    save_or_update_alert,
    acknowledge_alert,
    get_alerts_list,
    get_alert_by_id,
    export_alerts_to_csv_string
)
from backend.services.risk.official_warnings import (
    get_official_imd_warnings,
    IMD_MAIN_PORTAL,
    IMD_CHENNAI_PORTAL
)
from backend.services.risk.summary_service import (
    generate_bilingual_risk_summary
)
from backend.services.risk.alert_service import (
    evaluate_and_sync_district_alerts,
    evaluate_statewide_risk_overview,
    get_all_district_risk_summaries,
    get_single_district_bilingual_summary
)
