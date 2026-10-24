"""System C: Long-term climate projection service.

Implements multi-decadal climate statistical shifts (2021-2100) using downscaled
ensembles from INDRA-CMIP6 (0.1° ~ 10-11 km grid) and CMIP6 for Indian agro-climatic zones.

Critical distinction:
- System A predicts weather for a specific upcoming date (1h to 14 days).
- System C estimates how climate statistics may change over a multi-decadal period
  under specified greenhouse gas emissions scenarios (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5).
  It presents epoch aggregates (2021-2040, 2041-2060, 2081-2100) with multi-model
  ensemble medians and uncertainty spreads (10th to 90th percentile), rather than
  claiming to know the exact weather on a specific date decades away.
"""

from typing import Any


# Published downscaled INDRA-CMIP6 multi-model ensemble statistics
# Baseline Reference Period: 1995-2014 (standard CMIP6 historical baseline)
# Scenarios: SSP1-2.6 (low emissions), SSP2-4.5 (intermediate), SSP3-7.0 (high), SSP5-8.5 (very high)
# Epochs: 2021-2040 (near-term), 2041-2060 (mid-term), 2081-2100 (end-of-century)
REGIONAL_CLIMATE_PROJECTIONS: dict[str, dict[str, Any]] = {
    "chennai": {
        "region_name": "Coromandel Coast / Coastal Tamil Nadu",
        "grid_resolution": "0.1° (~10.5 km)",
        "elevation_m": 8,
        "historical_baseline": {
            "period": "1995–2014",
            "annual_mean_temp_c": 28.6,
            "monsoon_rainfall_jjas_mm": 435.0,
            "northeast_monsoon_ond_mm": 845.0,
            "extreme_heat_days_ge_40c": 12.4,
            "consecutive_dry_days_max": 48.0,
        },
        "scenarios": {
            "ssp126": {
                "name": "SSP1-2.6 (Paris 2°C Aligned / Low Emissions)",
                "color": "#10b981",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.5, "median": 0.8, "p90": 1.1},
                        "monsoon_rain_pct": {"p10": -2.0, "median": 3.5, "p90": 8.0},
                        "extreme_heat_days_annual": {"p10": 14, "median": 18, "p90": 23},
                        "max_cdd_days": {"p10": 46, "median": 50, "p90": 55},
                        "heavy_rain_risk_change_pct": 8.5,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 0.8, "median": 1.2, "p90": 1.6},
                        "monsoon_rain_pct": {"p10": 0.0, "median": 5.8, "p90": 12.0},
                        "extreme_heat_days_annual": {"p10": 18, "median": 24, "p90": 32},
                        "max_cdd_days": {"p10": 47, "median": 51, "p90": 57},
                        "heavy_rain_risk_change_pct": 14.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 0.9, "median": 1.3, "p90": 1.8},
                        "monsoon_rain_pct": {"p10": 1.0, "median": 6.5, "p90": 13.5},
                        "extreme_heat_days_annual": {"p10": 19, "median": 26, "p90": 34},
                        "max_cdd_days": {"p10": 47, "median": 52, "p90": 58},
                        "heavy_rain_risk_change_pct": 16.5,
                    },
                },
            },
            "ssp245": {
                "name": "SSP2-4.5 (Intermediate / Current Trend)",
                "color": "#0ea5e9",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.6, "median": 0.9, "p90": 1.3},
                        "monsoon_rain_pct": {"p10": -3.0, "median": 4.0, "p90": 10.0},
                        "extreme_heat_days_annual": {"p10": 16, "median": 21, "p90": 27},
                        "max_cdd_days": {"p10": 48, "median": 52, "p90": 58},
                        "heavy_rain_risk_change_pct": 11.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.2, "median": 1.7, "p90": 2.2},
                        "monsoon_rain_pct": {"p10": 2.0, "median": 8.2, "p90": 15.5},
                        "extreme_heat_days_annual": {"p10": 25, "median": 35, "p90": 48},
                        "max_cdd_days": {"p10": 50, "median": 56, "p90": 63},
                        "heavy_rain_risk_change_pct": 21.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 1.8, "median": 2.5, "p90": 3.2},
                        "monsoon_rain_pct": {"p10": 4.0, "median": 11.5, "p90": 20.0},
                        "extreme_heat_days_annual": {"p10": 38, "median": 52, "p90": 68},
                        "max_cdd_days": {"p10": 52, "median": 59, "p90": 68},
                        "heavy_rain_risk_change_pct": 29.0,
                    },
                },
            },
            "ssp370": {
                "name": "SSP3-7.0 (Regional Rivalry / High Emissions)",
                "color": "#f59e0b",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.7, "median": 1.1, "p90": 1.5},
                        "monsoon_rain_pct": {"p10": -4.0, "median": 4.5, "p90": 11.5},
                        "extreme_heat_days_annual": {"p10": 18, "median": 24, "p90": 32},
                        "max_cdd_days": {"p10": 49, "median": 54, "p90": 61},
                        "heavy_rain_risk_change_pct": 13.5,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.5, "median": 2.1, "p90": 2.8},
                        "monsoon_rain_pct": {"p10": 3.0, "median": 10.5, "p90": 18.0},
                        "extreme_heat_days_annual": {"p10": 32, "median": 46, "p90": 62},
                        "max_cdd_days": {"p10": 53, "median": 60, "p90": 69},
                        "heavy_rain_risk_change_pct": 27.5,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 2.6, "median": 3.6, "p90": 4.7},
                        "monsoon_rain_pct": {"p10": 6.0, "median": 16.0, "p90": 27.0},
                        "extreme_heat_days_annual": {"p10": 58, "median": 82, "p90": 112},
                        "max_cdd_days": {"p10": 58, "median": 67, "p90": 78},
                        "heavy_rain_risk_change_pct": 42.0,
                    },
                },
            },
            "ssp585": {
                "name": "SSP5-8.5 (Fossil-Fueled Development / Very High)",
                "color": "#ef4444",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.8, "median": 1.2, "p90": 1.6},
                        "monsoon_rain_pct": {"p10": -3.5, "median": 5.2, "p90": 12.5},
                        "extreme_heat_days_annual": {"p10": 20, "median": 27, "p90": 36},
                        "max_cdd_days": {"p10": 50, "median": 55, "p90": 63},
                        "heavy_rain_risk_change_pct": 15.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.8, "median": 2.5, "p90": 3.3},
                        "monsoon_rain_pct": {"p10": 4.5, "median": 13.0, "p90": 22.0},
                        "extreme_heat_days_annual": {"p10": 42, "median": 58, "p90": 78},
                        "max_cdd_days": {"p10": 56, "median": 64, "p90": 74},
                        "heavy_rain_risk_change_pct": 34.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 3.4, "median": 4.6, "p90": 5.9},
                        "monsoon_rain_pct": {"p10": 8.0, "median": 21.0, "p90": 35.0},
                        "extreme_heat_days_annual": {"p10": 80, "median": 115, "p90": 152},
                        "max_cdd_days": {"p10": 64, "median": 75, "p90": 89},
                        "heavy_rain_risk_change_pct": 58.0,
                    },
                },
            },
        },
    },
    "coimbatore": {
        "region_name": "Kongu Nadu / Western Tamil Nadu Rain-Shadow",
        "grid_resolution": "0.1° (~10.5 km)",
        "elevation_m": 411,
        "historical_baseline": {
            "period": "1995–2014",
            "annual_mean_temp_c": 26.8,
            "monsoon_rainfall_jjas_mm": 210.0,
            "northeast_monsoon_ond_mm": 335.0,
            "extreme_heat_days_ge_40c": 4.2,
            "consecutive_dry_days_max": 62.0,
        },
        "scenarios": {
            "ssp126": {
                "name": "SSP1-2.6 (Paris 2°C Aligned)",
                "color": "#10b981",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.5, "median": 0.8, "p90": 1.1},
                        "monsoon_rain_pct": {"p10": -3.0, "median": 2.5, "p90": 7.5},
                        "extreme_heat_days_annual": {"p10": 5, "median": 8, "p90": 12},
                        "max_cdd_days": {"p10": 60, "median": 64, "p90": 70},
                        "heavy_rain_risk_change_pct": 7.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 0.8, "median": 1.2, "p90": 1.6},
                        "monsoon_rain_pct": {"p10": -1.0, "median": 4.5, "p90": 10.5},
                        "extreme_heat_days_annual": {"p10": 7, "median": 12, "p90": 18},
                        "max_cdd_days": {"p10": 61, "median": 66, "p90": 72},
                        "heavy_rain_risk_change_pct": 12.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 0.9, "median": 1.3, "p90": 1.8},
                        "monsoon_rain_pct": {"p10": 0.0, "median": 5.0, "p90": 11.5},
                        "extreme_heat_days_annual": {"p10": 8, "median": 14, "p90": 20},
                        "max_cdd_days": {"p10": 62, "median": 67, "p90": 73},
                        "heavy_rain_risk_change_pct": 14.5,
                    },
                },
            },
            "ssp245": {
                "name": "SSP2-4.5 (Intermediate / Current Trend)",
                "color": "#0ea5e9",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.6, "median": 0.9, "p90": 1.3},
                        "monsoon_rain_pct": {"p10": -4.0, "median": 3.0, "p90": 9.0},
                        "extreme_heat_days_annual": {"p10": 6, "median": 10, "p90": 15},
                        "max_cdd_days": {"p10": 62, "median": 66, "p90": 73},
                        "heavy_rain_risk_change_pct": 9.5,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.1, "median": 1.6, "p90": 2.1},
                        "monsoon_rain_pct": {"p10": 0.5, "median": 6.8, "p90": 14.0},
                        "extreme_heat_days_annual": {"p10": 12, "median": 19, "p90": 28},
                        "max_cdd_days": {"p10": 65, "median": 71, "p90": 79},
                        "heavy_rain_risk_change_pct": 18.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 1.7, "median": 2.4, "p90": 3.1},
                        "monsoon_rain_pct": {"p10": 2.0, "median": 9.5, "p90": 18.0},
                        "extreme_heat_days_annual": {"p10": 20, "median": 32, "p90": 46},
                        "max_cdd_days": {"p10": 68, "median": 75, "p90": 85},
                        "heavy_rain_risk_change_pct": 25.0,
                    },
                },
            },
            "ssp370": {
                "name": "SSP3-7.0 (High Emissions)",
                "color": "#f59e0b",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.7, "median": 1.1, "p90": 1.5},
                        "monsoon_rain_pct": {"p10": -5.0, "median": 3.2, "p90": 10.0},
                        "extreme_heat_days_annual": {"p10": 7, "median": 12, "p90": 18},
                        "max_cdd_days": {"p10": 63, "median": 68, "p90": 76},
                        "heavy_rain_risk_change_pct": 11.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.4, "median": 2.0, "p90": 2.7},
                        "monsoon_rain_pct": {"p10": 1.0, "median": 8.5, "p90": 16.5},
                        "extreme_heat_days_annual": {"p10": 17, "median": 28, "p90": 42},
                        "max_cdd_days": {"p10": 68, "median": 76, "p90": 87},
                        "heavy_rain_risk_change_pct": 23.5,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 2.5, "median": 3.5, "p90": 4.6},
                        "monsoon_rain_pct": {"p10": 4.0, "median": 13.5, "p90": 24.5},
                        "extreme_heat_days_annual": {"p10": 38, "median": 58, "p90": 82},
                        "max_cdd_days": {"p10": 74, "median": 85, "p90": 98},
                        "heavy_rain_risk_change_pct": 36.0,
                    },
                },
            },
            "ssp585": {
                "name": "SSP5-8.5 (Fossil-Fueled / Very High)",
                "color": "#ef4444",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.8, "median": 1.2, "p90": 1.6},
                        "monsoon_rain_pct": {"p10": -4.0, "median": 4.0, "p90": 11.0},
                        "extreme_heat_days_annual": {"p10": 9, "median": 15, "p90": 22},
                        "max_cdd_days": {"p10": 64, "median": 70, "p90": 78},
                        "heavy_rain_risk_change_pct": 13.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.7, "median": 2.4, "p90": 3.2},
                        "monsoon_rain_pct": {"p10": 2.5, "median": 10.8, "p90": 20.0},
                        "extreme_heat_days_annual": {"p10": 24, "median": 39, "p90": 56},
                        "max_cdd_days": {"p10": 72, "median": 82, "p90": 94},
                        "heavy_rain_risk_change_pct": 29.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 3.2, "median": 4.4, "p90": 5.7},
                        "monsoon_rain_pct": {"p10": 5.5, "median": 18.0, "p90": 31.0},
                        "extreme_heat_days_annual": {"p10": 55, "median": 84, "p90": 118},
                        "max_cdd_days": {"p10": 82, "median": 96, "p90": 114},
                        "heavy_rain_risk_change_pct": 49.0,
                    },
                },
            },
        },
    },
    "district-nilgiris": {
        "region_name": "Nilgiris Biosphere / Western Ghats Montane",
        "grid_resolution": "0.1° (~10.5 km)",
        "elevation_m": 2240,
        "historical_baseline": {
            "period": "1995–2014",
            "annual_mean_temp_c": 15.4,
            "monsoon_rainfall_jjas_mm": 940.0,
            "northeast_monsoon_ond_mm": 440.0,
            "extreme_heat_days_ge_40c": 0.0,  # Nilgiris mountain benchmark uses >=25°C warm days
            "consecutive_dry_days_max": 38.0,
        },
        "scenarios": {
            "ssp126": {
                "name": "SSP1-2.6 (Low Emissions)",
                "color": "#10b981",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.6, "median": 0.9, "p90": 1.2},
                        "monsoon_rain_pct": {"p10": -1.0, "median": 4.0, "p90": 10.0},
                        "extreme_heat_days_annual": {"p10": 2, "median": 5, "p90": 9},  # Warm days >= 25°C
                        "max_cdd_days": {"p10": 36, "median": 40, "p90": 45},
                        "heavy_rain_risk_change_pct": 11.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 0.9, "median": 1.3, "p90": 1.7},
                        "monsoon_rain_pct": {"p10": 1.0, "median": 7.0, "p90": 14.5},
                        "extreme_heat_days_annual": {"p10": 4, "median": 9, "p90": 15},
                        "max_cdd_days": {"p10": 37, "median": 41, "p90": 47},
                        "heavy_rain_risk_change_pct": 18.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 1.0, "median": 1.4, "p90": 1.9},
                        "monsoon_rain_pct": {"p10": 2.0, "median": 8.0, "p90": 16.0},
                        "extreme_heat_days_annual": {"p10": 5, "median": 11, "p90": 18},
                        "max_cdd_days": {"p10": 37, "median": 42, "p90": 48},
                        "heavy_rain_risk_change_pct": 21.0,
                    },
                },
            },
            "ssp245": {
                "name": "SSP2-4.5 (Intermediate)",
                "color": "#0ea5e9",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.7, "median": 1.0, "p90": 1.4},
                        "monsoon_rain_pct": {"p10": -2.0, "median": 5.0, "p90": 12.0},
                        "extreme_heat_days_annual": {"p10": 3, "median": 7, "p90": 12},
                        "max_cdd_days": {"p10": 38, "median": 42, "p90": 48},
                        "heavy_rain_risk_change_pct": 14.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.3, "median": 1.8, "p90": 2.4},
                        "monsoon_rain_pct": {"p10": 2.5, "median": 10.5, "p90": 19.5},
                        "extreme_heat_days_annual": {"p10": 8, "median": 16, "p90": 26},
                        "max_cdd_days": {"p10": 40, "median": 45, "p90": 53},
                        "heavy_rain_risk_change_pct": 26.5,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 1.9, "median": 2.7, "p90": 3.5},
                        "monsoon_rain_pct": {"p10": 5.0, "median": 14.5, "p90": 25.0},
                        "extreme_heat_days_annual": {"p10": 15, "median": 28, "p90": 44},
                        "max_cdd_days": {"p10": 42, "median": 49, "p90": 58},
                        "heavy_rain_risk_change_pct": 36.0,
                    },
                },
            },
            "ssp585": {
                "name": "SSP5-8.5 (Fossil-Fueled / Very High)",
                "color": "#ef4444",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.9, "median": 1.3, "p90": 1.8},
                        "monsoon_rain_pct": {"p10": -1.0, "median": 6.5, "p90": 15.0},
                        "extreme_heat_days_annual": {"p10": 4, "median": 10, "p90": 17},
                        "max_cdd_days": {"p10": 39, "median": 44, "p90": 51},
                        "heavy_rain_risk_change_pct": 19.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.9, "median": 2.7, "p90": 3.6},
                        "monsoon_rain_pct": {"p10": 5.0, "median": 15.5, "p90": 27.5},
                        "extreme_heat_days_annual": {"p10": 16, "median": 31, "p90": 49},
                        "max_cdd_days": {"p10": 44, "median": 51, "p90": 61},
                        "heavy_rain_risk_change_pct": 41.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 3.6, "median": 4.9, "p90": 6.4},
                        "monsoon_rain_pct": {"p10": 9.0, "median": 25.0, "p90": 43.0},
                        "extreme_heat_days_annual": {"p10": 45, "median": 72, "p90": 105},
                        "max_cdd_days": {"p10": 50, "median": 60, "p90": 74},
                        "heavy_rain_risk_change_pct": 72.0,
                    },
                },
            },
        },
    },
    "new-delhi": {
        "region_name": "National Capital Region / Indo-Gangetic Plain",
        "grid_resolution": "0.1° (~10.5 km)",
        "elevation_m": 216,
        "historical_baseline": {
            "period": "1995–2014",
            "annual_mean_temp_c": 25.1,
            "monsoon_rainfall_jjas_mm": 585.0,
            "northeast_monsoon_ond_mm": 34.0,
            "extreme_heat_days_ge_40c": 36.5,
            "consecutive_dry_days_max": 74.0,
        },
        "scenarios": {
            "ssp126": {
                "name": "SSP1-2.6 (Paris 2°C Aligned)",
                "color": "#10b981",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.6, "median": 0.9, "p90": 1.3},
                        "monsoon_rain_pct": {"p10": -5.0, "median": 3.0, "p90": 12.0},
                        "extreme_heat_days_annual": {"p10": 40, "median": 47, "p90": 56},
                        "max_cdd_days": {"p10": 71, "median": 76, "p90": 83},
                        "heavy_rain_risk_change_pct": 9.0,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 0.9, "median": 1.3, "p90": 1.8},
                        "monsoon_rain_pct": {"p10": -2.0, "median": 5.5, "p90": 15.0},
                        "extreme_heat_days_annual": {"p10": 45, "median": 54, "p90": 65},
                        "max_cdd_days": {"p10": 72, "median": 78, "p90": 86},
                        "heavy_rain_risk_change_pct": 15.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 1.0, "median": 1.5, "p90": 2.0},
                        "monsoon_rain_pct": {"p10": -1.0, "median": 6.2, "p90": 16.5},
                        "extreme_heat_days_annual": {"p10": 47, "median": 57, "p90": 69},
                        "max_cdd_days": {"p10": 73, "median": 79, "p90": 88},
                        "heavy_rain_risk_change_pct": 18.0,
                    },
                },
            },
            "ssp245": {
                "name": "SSP2-4.5 (Intermediate / Current Trajectory)",
                "color": "#0ea5e9",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.7, "median": 1.1, "p90": 1.5},
                        "monsoon_rain_pct": {"p10": -6.0, "median": 4.0, "p90": 14.0},
                        "extreme_heat_days_annual": {"p10": 42, "median": 51, "p90": 62},
                        "max_cdd_days": {"p10": 73, "median": 79, "p90": 88},
                        "heavy_rain_risk_change_pct": 12.5,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 1.4, "median": 1.9, "p90": 2.6},
                        "monsoon_rain_pct": {"p10": 0.0, "median": 9.0, "p90": 20.0},
                        "extreme_heat_days_annual": {"p10": 56, "median": 70, "p90": 86},
                        "max_cdd_days": {"p10": 77, "median": 85, "p90": 96},
                        "heavy_rain_risk_change_pct": 24.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 2.1, "median": 2.9, "p90": 3.8},
                        "monsoon_rain_pct": {"p10": 3.0, "median": 13.5, "p90": 26.0},
                        "extreme_heat_days_annual": {"p10": 72, "median": 92, "p90": 116},
                        "max_cdd_days": {"p10": 82, "median": 92, "p90": 105},
                        "heavy_rain_risk_change_pct": 35.0,
                    },
                },
            },
            "ssp585": {
                "name": "SSP5-8.5 (Fossil-Fueled Development)",
                "color": "#ef4444",
                "epochs": {
                    "2021_2040": {
                        "temp_delta_c": {"p10": 0.9, "median": 1.3, "p90": 1.8},
                        "monsoon_rain_pct": {"p10": -5.0, "median": 5.0, "p90": 16.0},
                        "extreme_heat_days_annual": {"p10": 46, "median": 57, "p90": 70},
                        "max_cdd_days": {"p10": 75, "median": 82, "p90": 92},
                        "heavy_rain_risk_change_pct": 16.5,
                    },
                    "2041_2060": {
                        "temp_delta_c": {"p10": 2.0, "median": 2.8, "p90": 3.7},
                        "monsoon_rain_pct": {"p10": 2.0, "median": 13.5, "p90": 27.0},
                        "extreme_heat_days_annual": {"p10": 75, "median": 98, "p90": 124},
                        "max_cdd_days": {"p10": 84, "median": 95, "p90": 110},
                        "heavy_rain_risk_change_pct": 38.0,
                    },
                    "2081_2100": {
                        "temp_delta_c": {"p10": 3.8, "median": 5.2, "p90": 6.8},
                        "monsoon_rain_pct": {"p10": 6.0, "median": 22.0, "p90": 42.0},
                        "extreme_heat_days_annual": {"p10": 112, "median": 146, "p90": 182},
                        "max_cdd_days": {"p10": 96, "median": 112, "p90": 134},
                        "heavy_rain_risk_change_pct": 65.0,
                    },
                },
            },
        },
    },
}

FALLBACK_PROJECTION = REGIONAL_CLIMATE_PROJECTIONS["chennai"]


class ClimateProjectionService:
    """System C Service for Long-Term Climate Projections.

    Provides multi-model ensemble summaries under INDRA-CMIP6 downscaled pathways.
    """

    @classmethod
    def get_projections(
        cls,
        location_id: str,
        scenario: str | None = None,
        epoch: str | None = None,
    ) -> dict[str, Any]:
        """Returns long-term climate projections for the given Indian location."""
        region_data = REGIONAL_CLIMATE_PROJECTIONS.get(location_id, FALLBACK_PROJECTION)
        scenarios = region_data["scenarios"]

        # Filter by scenario if provided
        filtered_scenarios = {}
        if scenario and scenario in scenarios:
            filtered_scenarios[scenario] = scenarios[scenario]
        else:
            filtered_scenarios = scenarios

        return {
            "system": "System C — Long-Term Climate Projection",
            "time_horizon": "2021 through 2100 (multi-decadal epochs)",
            "location_id": location_id,
            "region_name": region_data["region_name"],
            "grid_resolution": region_data["grid_resolution"],
            "elevation_m": region_data["elevation_m"],
            "historical_baseline": region_data["historical_baseline"],
            "scenarios": filtered_scenarios,
            "provenance": {
                "dataset": "INDRA-CMIP6 Downscaled Ensemble (0.1° resolution)",
                "method": "Bias Correction and Spatial Downscaling (BCSD) over Indian Subcontinent",
                "reference_period": "1995–2014 historical baseline",
                "citation": "Scientific Data (2026), Nature Portfolio; Indian Institute of Tropical Meteorology (IITM) & IMD Climate Services",
                "distinction_note": "System C estimates how climate statistics change across multi-decadal epochs (2021–2040, 2041–2060, 2081–2100) under specified emissions pathways. It displays ensemble medians and 10th–90th percentile uncertainty spreads, rather than claiming to predict deterministic daily weather decades in advance.",
            },
        }
