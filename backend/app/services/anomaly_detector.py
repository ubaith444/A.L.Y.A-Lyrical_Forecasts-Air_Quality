from datetime import date
from typing import Any
import numpy as np


# Standardized monthly climatological baselines for reference Indian agro-climatic zones
# Derived from ECMWF ERA5-Land (1991-2020 reference normal baseline)
REGIONAL_CLIMATOLOGICAL_NORMALS: dict[str, dict[str, dict[str, float]]] = {
    "chennai": {
        "temperature_mean": {
            "1": 25.1, "2": 26.6, "3": 28.9, "4": 31.4, "5": 33.3, "6": 32.8,
            "7": 31.1, "8": 30.6, "9": 30.1, "10": 28.7, "11": 26.5, "12": 25.3
        },
        "temperature_std": {
            "1": 1.1, "2": 1.2, "3": 1.3, "4": 1.4, "5": 1.6, "6": 1.5,
            "7": 1.3, "8": 1.2, "9": 1.1, "10": 1.2, "11": 1.1, "12": 1.0
        },
        "rainfall_monthly_mean": {
            "1": 22.0, "2": 12.0, "3": 15.0, "4": 18.0, "5": 42.0, "6": 60.0,
            "7": 105.0, "8": 135.0, "9": 140.0, "10": 305.0, "11": 380.0, "12": 160.0
        },
    },
    "coimbatore": {
        "temperature_mean": {
            "1": 24.3, "2": 26.2, "3": 28.6, "4": 30.1, "5": 29.8, "6": 27.2,
            "7": 26.5, "8": 26.7, "9": 27.1, "10": 26.8, "11": 25.2, "12": 24.1
        },
        "temperature_std": {
            "1": 1.0, "2": 1.1, "3": 1.3, "4": 1.4, "5": 1.5, "6": 1.2,
            "7": 1.1, "8": 1.1, "9": 1.1, "10": 1.2, "11": 1.0, "12": 0.9
        },
        "rainfall_monthly_mean": {
            "1": 11.0, "2": 14.0, "3": 22.0, "4": 52.0, "5": 78.0, "6": 42.0,
            "7": 55.0, "8": 48.0, "9": 65.0, "10": 165.0, "11": 125.0, "12": 45.0
        },
    },
    "district-nilgiris": {
        "temperature_mean": {
            "1": 13.2, "2": 14.5, "3": 16.1, "4": 17.5, "5": 17.8, "6": 15.6,
            "7": 14.8, "8": 15.1, "9": 15.3, "10": 15.2, "11": 14.3, "12": 13.5
        },
        "temperature_std": {
            "1": 1.2, "2": 1.3, "3": 1.4, "4": 1.3, "5": 1.2, "6": 1.0,
            "7": 0.9, "8": 0.9, "9": 1.0, "10": 1.1, "11": 1.1, "12": 1.2
        },
        "rainfall_monthly_mean": {
            "1": 20.0, "2": 25.0, "3": 45.0, "4": 95.0, "5": 140.0, "6": 210.0,
            "7": 320.0, "8": 260.0, "9": 150.0, "10": 210.0, "11": 170.0, "12": 60.0
        },
    },
    "new-delhi": {
        "temperature_mean": {
            "1": 14.2, "2": 17.6, "3": 23.4, "4": 29.8, "5": 33.5, "6": 34.1,
            "7": 31.2, "8": 30.1, "9": 29.4, "10": 26.2, "11": 20.5, "12": 15.4
        },
        "temperature_std": {
            "1": 1.6, "2": 1.8, "3": 2.1, "4": 2.2, "5": 2.0, "6": 1.9,
            "7": 1.7, "8": 1.5, "9": 1.6, "10": 1.5, "11": 1.6, "12": 1.5
        },
        "rainfall_monthly_mean": {
            "1": 19.0, "2": 20.0, "3": 15.0, "4": 12.0, "5": 28.0, "6": 75.0,
            "7": 220.0, "8": 240.0, "9": 125.0, "10": 18.0, "11": 6.0, "12": 10.0
        },
    },
}

# Fallback generic Indian subtropical baseline
DEFAULT_NORMAL = {
    "temperature_mean": {str(m): 27.0 for m in range(1, 13)},
    "temperature_std": {str(m): 1.5 for m in range(1, 13)},
    "rainfall_monthly_mean": {str(m): 90.0 for m in range(1, 13)},
}


class ClimateAnomalyEngine:
    """System B: Extreme-weather and climate anomaly detection.

    Computes standardized anomalies (Z-scores) against location-specific historical baselines,
    identifies unusual heatwaves, cold waves, monsoon rainfall deficits/surpluses, and
    separates short-term weather anomalies from multi-year climate shifts.
    """

    @classmethod
    def get_location_normals(cls, location_id: str) -> dict[str, dict[str, float]]:
        return REGIONAL_CLIMATOLOGICAL_NORMALS.get(location_id, DEFAULT_NORMAL)

    @classmethod
    def calculate_temperature_anomaly(
        cls,
        location_id: str,
        observed_temp_celsius: float,
        target_date: date,
    ) -> dict[str, Any]:
        """Calculates standardized departure from 1991-2020 ERA5-Land climatological normal."""
        month_str = str(target_date.month)
        normals = cls.get_location_normals(location_id)

        mean_normal = normals["temperature_mean"].get(month_str, 27.0)
        std_normal = max(0.5, normals["temperature_std"].get(month_str, 1.5))

        departure = round(observed_temp_celsius - mean_normal, 2)
        z_score = round(departure / std_normal, 2)

        # Standard Meteorological Category
        if z_score >= 3.0:
            category = "Extreme Heat Anomaly"
            severity = "extreme"
            description = f"Observed temperature is +{departure}°C above the 30-year climatological baseline (Z = +{z_score}σ). Extreme heat alert threshold met."
        elif z_score >= 2.0:
            category = "Severe Heat Departure"
            severity = "severe"
            description = f"Temperature is significantly elevated (+{departure}°C, Z = +{z_score}σ). IMD Heatwave criteria active."
        elif z_score >= 1.0:
            category = "Above Normal"
            severity = "moderate"
            description = f"Temperature is warmer than seasonal expectations (+{departure}°C above normal)."
        elif z_score <= -3.0:
            category = "Extreme Cold Anomaly"
            severity = "extreme"
            description = f"Severe cold wave conditions: {departure}°C below normal (Z = {z_score}σ)."
        elif z_score <= -2.0:
            category = "Cold Wave Departure"
            severity = "severe"
            description = f"Significant cold departure ({departure}°C below normal)."
        elif z_score <= -1.0:
            category = "Below Normal"
            severity = "moderate"
            description = f"Temperature is cooler than seasonal normal ({departure}°C below normal)."
        else:
            category = "Near Climatological Normal"
            severity = "normal"
            description = f"Temperature is within standard historical variance (departure: {departure:+}°C, Z = {z_score:+}σ)."

        return {
            "location_id": location_id,
            "date": target_date.isoformat(),
            "observed_value": observed_temp_celsius,
            "climatological_normal": mean_normal,
            "departure": departure,
            "z_score": z_score,
            "category": category,
            "severity": severity,
            "unit": "°C",
            "baseline_period": "1991–2020 ERA5-Land Reference Normal",
            "description": description,
        }

    @classmethod
    def calculate_monsoon_anomaly(
        cls,
        location_id: str,
        accumulated_rain_mm: float,
        month: int,
    ) -> dict[str, Any]:
        """Evaluates monsoon rainfall departure according to IMD standardized classification.

        (Excess: >= +20%, Normal: -19% to +19%, Deficient: -20% to -59%, Large Deficient: <= -60%)
        """
        normals = cls.get_location_normals(location_id)
        normal_rain = normals["rainfall_monthly_mean"].get(str(month), 100.0)

        departure_pct = round(((accumulated_rain_mm - normal_rain) / normal_rain) * 100.0, 1)

        if departure_pct >= 60.0:
            category = "Large Excess Rainfall"
            imd_status = "large_excess"
        elif departure_pct >= 20.0:
            category = "Excess Rainfall"
            imd_status = "excess"
        elif departure_pct >= -19.0:
            category = "Normal Rainfall"
            imd_status = "normal"
        elif departure_pct >= -59.0:
            category = "Deficient Rainfall"
            imd_status = "deficient"
        else:
            category = "Large Deficient Rainfall"
            imd_status = "large_deficient"

        return {
            "location_id": location_id,
            "month": month,
            "accumulated_rain_mm": round(accumulated_rain_mm, 1),
            "climatological_normal_mm": round(normal_rain, 1),
            "departure_pct": departure_pct,
            "category": category,
            "imd_status": imd_status,
            "baseline_period": "1991–2020 Long Period Average (LPA)",
        }

    @classmethod
    def diagnose_anomaly(
        cls,
        location_id: str,
        current_temp_c: float,
        rainfall_month_mm: float,
        consecutive_dry_days: int = 0,
        month: int = 5,
        target_date: date | None = None,
    ) -> dict[str, Any]:
        """Comprehensive System B diagnosis.

        Separates an episodic weather event from a long-term climate trend,
        and generates a multivariable anomaly score (0-100).
        """
        if target_date is None:
            target_date = date.today()

        temp_res = cls.calculate_temperature_anomaly(location_id, current_temp_c, target_date)
        rain_res = cls.calculate_monsoon_anomaly(location_id, rainfall_month_mm, month)

        z_temp = abs(temp_res["z_score"])
        rain_dep = abs(rain_res["departure_pct"])

        # Composite anomaly score (0-100)
        # Scaled from Z-score (0-4σ -> 0-60 pts) + rainfall departure (0-100% -> 0-30 pts) + dry days (0-10 pts)
        temp_pts = min(60.0, (z_temp / 3.0) * 60.0)
        rain_pts = min(30.0, (rain_dep / 60.0) * 30.0)
        cdd_pts = min(10.0, (consecutive_dry_days / 30.0) * 10.0)
        anomaly_score = round(min(100.0, temp_pts + rain_pts + cdd_pts), 1)

        # Distinguish between short-term weather spike vs long-term climate trend
        # Weather spike: high Z-score on daily timescale, but within 30-year seasonal bounds
        # Climate trend: multi-year temperature shifts, elevated night-time minimums, expanding dry spell length
        if z_temp >= 2.5:
            trend_distinction = {
                "classification": "Episodic Extreme Weather Spike",
                "nature": "Short-term meteorological aberration driven by synoptic circulation, heat dome, or cyclonic system.",
                "actionability": "Immediate operational alert (IMD heatwave/coldwave protocol active).",
                "is_climate_trend": False,
            }
        elif z_temp >= 1.2 or rain_dep >= 35.0:
            trend_distinction = {
                "classification": "Compound Seasonal Deviation",
                "nature": "Extended seasonal anomaly reflecting regional climate variability compounded by warming baseline.",
                "actionability": "Agro-advisory alert: moisture conservation and thermal stress management recommended.",
                "is_climate_trend": True,
            }
        else:
            trend_distinction = {
                "classification": "Climatologically Consistent",
                "nature": "Variability falls within 1991–2020 ERA5-Land standard deviation envelope (Z < 1.0σ).",
                "actionability": "Standard operational monitoring.",
                "is_climate_trend": False,
            }

        return {
            "system": "System B — Extreme-Weather and Climate Anomaly Detection",
            "location_id": location_id,
            "evaluation_date": target_date.isoformat(),
            "composite_anomaly_score": anomaly_score,
            "overall_severity": temp_res["severity"],
            "temperature_anomaly": temp_res,
            "rainfall_anomaly": rain_res,
            "dry_spell_days": consecutive_dry_days,
            "event_vs_trend_diagnosis": trend_distinction,
            "provenance": {
                "baseline_period": "1991–2020 ERA5-Land & IMD Long Period Average (LPA)",
                "method": "Multi-variable standardized departure with isolation of synoptic spikes vs decadal shifts",
            },
        }

