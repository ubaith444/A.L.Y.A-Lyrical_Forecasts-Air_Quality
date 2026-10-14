"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 5: Risk Intelligence — Thresholds Configuration

Defines transparent, configurable risk thresholds across 4 operational vectors:
1. Heavy Rainfall (Precipitation depth & intensity)
2. Extreme Heat (Temperature & Heat Index)
3. Strong Wind & Squall (Sustained speed & Gusts)
4. Prolonged Dry Spells (Consecutive dry days)

Distinguishes application-configurable risk thresholds from official IMD warning criteria.
"""

from typing import Dict, Any, List

# 4-Tier Risk Levels
SEVERITY_LEVELS = ["Low", "Moderate", "High", "Severe"]

# Application Configurable Risk Thresholds
APPLICATION_THRESHOLDS: Dict[str, Any] = {
    "rainfall": {
        "name": "Heavy Rainfall Risk",
        "variable": "precipitation_sum_24h_mm",
        "unit": "mm",
        "levels": {
            "Low": {"min": 0.0, "max": 15.5, "desc": "Light or localized showers"},
            "Moderate": {"min": 15.6, "max": 64.4, "desc": "Moderate rain with localized surface pooling"},
            "High": {"min": 64.5, "max": 115.5, "desc": "Heavy rainfall (IMD Heavy Rain threshold exceeded)"},
            "Severe": {"min": 115.6, "max": 999.0, "desc": "Very heavy to extremely heavy rainfall with inundation risk"}
        }
    },
    "heat": {
        "name": "Extreme Heat & Thermal Stress",
        "variable": "heat_index_celsius",
        "unit": "°C",
        "levels": {
            "Low": {"min": 0.0, "max": 31.9, "desc": "Thermal comfort zone with minimal heat stress"},
            "Moderate": {"min": 32.0, "max": 40.9, "desc": "Moderate thermal discomfort; prolonged activity requires hydration"},
            "High": {"min": 41.0, "max": 51.0, "desc": "Extreme caution: cramps and heat exhaustion possible with physical exertion"},
            "Severe": {"min": 51.1, "max": 100.0, "desc": "Danger: heatstroke imminent with continued exposure"}
        },
        "air_temperature_override": {
            "Severe": 42.0,  # Any dry-bulb temp >= 42°C is Severe heatwave
            "High": 39.0
        }
    },
    "wind": {
        "name": "High Wind & Cyclonic Gusts",
        "variable": "wind_gusts_max_kmh",
        "unit": "km/h",
        "levels": {
            "Low": {"min": 0.0, "max": 29.9, "desc": "Gentle to moderate coastal/plains breeze"},
            "Moderate": {"min": 30.0, "max": 50.0, "desc": "Fresh to strong breeze; minor tree swaying"},
            "High": {"min": 50.1, "max": 70.0, "desc": "Near gale to gale force; danger to thatched structures & fishing craft"},
            "Severe": {"min": 70.1, "max": 999.0, "desc": "Storm to violent squall; structural damage and uprooting risk"}
        }
    },
    "dry_spell": {
        "name": "Prolonged Agricultural Dry Spell",
        "variable": "consecutive_dry_days",
        "unit": "days",
        "levels": {
            "Low": {"min": 0, "max": 6, "desc": "Normal inter-spell moisture retention"},
            "Moderate": {"min": 7, "max": 13, "desc": "Mild moisture deficit; surface soil drying"},
            "High": {"min": 14, "max": 20, "desc": "Severe agricultural dry spell; crop moisture stress"},
            "Severe": {"min": 21, "max": 999, "desc": "Acute drought-like stress requiring supplemental irrigation"}
        }
    }
}

# Official IMD Warning Classification Criteria (Informational reference only)
# Strictly separated from application calculated risk.
IMD_WARNING_CRITERIA: Dict[str, Any] = {
    "agency": "India Meteorological Department (IMD) / Regional Meteorological Centre (RMC) Chennai",
    "portal_url": "https://mausam.imd.gov.in/chennai/",
    "warning_color_codes": {
        "Green": {
            "name": "No Warning",
            "action": "No specific action required. Weather conditions normal.",
            "rainfall_range": "< 64.5 mm",
            "hex": "#1b8a5a"
        },
        "Yellow": {
            "name": "Watch (Be Updated)",
            "action": "Severe weather possible. Keep abreast of local updates.",
            "rainfall_range": "64.5 mm to 115.5 mm (Isolated heavy rain)",
            "hex": "#d97706"
        },
        "Orange": {
            "name": "Alert (Be Prepared)",
            "action": "High likelihood of severe weather affecting transport and livelihoods. Prepare contingencies.",
            "rainfall_range": "115.6 mm to 204.4 mm (Very heavy rain)",
            "hex": "#ea580c"
        },
        "Red": {
            "name": "Warning (Take Action)",
            "action": "Extremely severe weather imminent with widespread disruption. Disaster response activated.",
            "rainfall_range": "≥ 204.5 mm (Extremely heavy rain)",
            "hex": "#dc2626"
        }
    }
}


def get_threshold_config() -> Dict[str, Any]:
    """Returns the combined active application and official IMD criteria metadata."""
    return {
        "application_thresholds": APPLICATION_THRESHOLDS,
        "imd_official_criteria": IMD_WARNING_CRITERIA,
        "disclaimer": (
            "Application-generated alerts are derived algorithmically using local topography "
            "and numerical weather estimates. They are strictly separate from official warnings "
            "issued by the India Meteorological Department (IMD)."
        )
    }
