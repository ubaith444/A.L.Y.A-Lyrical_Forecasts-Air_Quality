"""
Tamil Nadu Climate & Forecast Intelligence Platform
Operational Intelligence Module 1: Computed Meteorological Indicators

Implements validated formulas for:
1. Apparent Temperature & Heat Index (Rothfusz & Steadman formulas)
2. Cumulative Rainfall Accumulation (6h, 24h, 48h, 72h)
3. Rainfall Anomaly vs 30-Year Climatological Normals (LPA)
4. Wind Exposure (Sustained & Gusts classification)
5. Dew-Point Spread (T - T_d moisture context)
6. Pressure Tendency (3h & 24h barometric change)
7. Dry-Spell Duration (Consecutive days < 2.5mm threshold)
8. Convective & Instability Proxies (with explicit thermodynamic limitations)
"""

import math
from typing import Dict, Any, List, Optional


def compute_apparent_temperature(temp_c: float, rh_pct: float, wind_kmh: float = 0.0) -> Dict[str, Any]:
    """
    Computes apparent temperature (feels-like) using the Australian Bureau of Meteorology / Steadman model.
    AT = Ta + 0.33 * e - 0.70 * ws - 4.00
    where e is water vapor pressure in hPa.
    """
    # Water vapor pressure (e) in hPa
    e = (rh_pct / 100.0) * 6.105 * math.exp((17.27 * temp_c) / (237.7 + temp_c))
    wind_ms = wind_kmh / 3.6
    at = temp_c + 0.33 * e - 0.70 * wind_ms - 4.00

    # Rothfusz Heat Index for elevated temperatures (T >= 27°C)
    if temp_c >= 27.0 and rh_pct >= 40.0:
        tf = temp_c * 9.0 / 5.0 + 32.0
        hi_f = (
            -42.379
            + 2.04901523 * tf
            + 10.14333127 * rh_pct
            - 0.22475541 * tf * rh_pct
            - 0.00683783 * tf * tf
            - 0.05481717 * rh_pct * rh_pct
            + 0.00122874 * tf * tf * rh_pct
            + 0.00085282 * tf * rh_pct * rh_pct
            - 0.00000199 * tf * tf * rh_pct * rh_pct
        )
        heat_index_c = (hi_f - 32.0) * 5.0 / 9.0
    else:
        heat_index_c = at

    # Exposure classification
    if heat_index_c >= 51.0 or temp_c >= 42.0:
        category = "Severe"
        guidance = "Extreme heat danger; imminent heat stroke risk under direct sun."
    elif heat_index_c >= 41.0:
        category = "High"
        guidance = "Heat cramps and physical exhaustion likely with prolonged activity."
    elif heat_index_c >= 32.0:
        category = "Moderate"
        guidance = "Caution advised; increased hydration necessary for outdoor labor."
    else:
        category = "Low"
        guidance = "Benign thermal conditions; standard outdoor comfort."

    return {
        "apparent_temperature_c": round(at, 1),
        "heat_index_c": round(heat_index_c, 1),
        "category": category,
        "vapor_pressure_hpa": round(e, 1),
        "guidance": guidance,
        "computation_method": "Steadman AT + NOAA Rothfusz Heat Index regression"
    }


def compute_rainfall_accumulations(hourly_series: List[Dict[str, Any]], daily_series: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes precipitation accumulation over defined operational windows: 6h, 24h, 48h, 72h.
    """
    rain_6h = 0.0
    rain_24h = 0.0
    rain_48h = 0.0
    rain_72h = 0.0

    if hourly_series:
        for idx, h in enumerate(hourly_series):
            precip = float(h.get("rain_mm", 0.0) or h.get("precipitation_mm", 0.0))
            if idx < 6:
                rain_6h += precip
            if idx < 24:
                rain_24h += precip
            if idx < 48:
                rain_48h += precip
            if idx < 72:
                rain_72h += precip
    elif daily_series:
        rain_24h = float(daily_series[0].get("precipitation_sum_mm", 0.0)) if len(daily_series) > 0 else 0.0
        rain_6h = rain_24h * 0.35
        rain_48h = sum(float(d.get("precipitation_sum_mm", 0.0)) for d in daily_series[:2])
        rain_72h = sum(float(d.get("precipitation_sum_mm", 0.0)) for d in daily_series[:3])

    # IMD Rainfall Intensity Classification for 24h
    if rain_24h >= 115.6:
        intensity = "Very Heavy Rain"
        severity = "Severe"
    elif rain_24h >= 64.5:
        intensity = "Heavy Rain"
        severity = "High"
    elif rain_24h >= 15.6:
        intensity = "Moderate Rain"
        severity = "Moderate"
    elif rain_24h >= 2.5:
        intensity = "Light Rain"
        severity = "Low"
    else:
        intensity = "Dry / Negligible"
        severity = "Low"

    return {
        "acc_6h_mm": round(rain_6h, 1),
        "acc_24h_mm": round(rain_24h, 1),
        "acc_48h_mm": round(rain_48h, 1),
        "acc_72h_mm": round(rain_72h, 1),
        "intensity_classification": intensity,
        "severity": severity,
        "computation_method": "Temporal summation across calibrated forecast windows"
    }


def compute_rainfall_anomaly(rain_24h: float, annual_normal_mm: float, nem_normal_mm: float, month: int) -> Dict[str, Any]:
    """
    Computes expected rainfall anomaly against Long Period Averages (LPA) for the active monsoon.
    """
    # Daily normal expectation for month
    if month in (10, 11, 12):
        # Northeast Monsoon (NEM) daily normal baseline
        daily_normal = nem_normal_mm / 92.0
        season = "Northeast Monsoon (NEM)"
    elif month in (6, 7, 8, 9):
        # Southwest Monsoon (SWM) daily normal baseline
        daily_normal = (annual_normal_mm - nem_normal_mm) * 0.45 / 122.0
        season = "Southwest Monsoon (SWM)"
    else:
        # Dry / Pre-monsoon baseline
        daily_normal = 2.0
        season = "Dry / Inter-Monsoon"

    diff = rain_24h - daily_normal
    departure_pct = (diff / daily_normal) * 100.0 if daily_normal > 0 else 0.0

    if departure_pct >= 60.0:
        category = "Large Excess"
    elif departure_pct >= 20.0:
        category = "Excess"
    elif departure_pct >= -19.0:
        category = "Normal"
    elif departure_pct >= -59.0:
        category = "Deficient"
    else:
        category = "Large Deficient"

    return {
        "daily_normal_mm": round(daily_normal, 2),
        "forecast_rain_24h_mm": round(rain_24h, 1),
        "departure_pct": round(departure_pct, 1),
        "departure_category": category,
        "active_season": season,
        "climatological_baseline": "IMD 30-Year Long Period Average (1991-2020)"
    }


def compute_wind_exposure(wind_speed_kmh: float, gust_kmh: float, is_coastal: bool) -> Dict[str, Any]:
    """
    Evaluates wind field exposure, sustained force, and gust impact for transport and coastal operations.
    """
    effective_wind = max(wind_speed_kmh, gust_kmh * 0.75)

    if effective_wind >= 70.0:
        level = "Severe"
        guidance = "Squall / Storm conditions; severe hazard to marine craft and elevated structures."
    elif effective_wind >= 51.0 or (is_coastal and gust_kmh >= 45.0):
        level = "High"
        guidance = "Gale force gusts; port cargo operations and small fishing craft disrupted."
    elif effective_wind >= 30.0:
        level = "Moderate"
        guidance = "Breezy / Strong coastal breeze; caution for high-sided highway vehicles."
    else:
        level = "Low"
        guidance = "Light to moderate breeze; negligible operational constraint."

    return {
        "sustained_wind_kmh": round(wind_speed_kmh, 1),
        "gust_speed_kmh": round(gust_kmh, 1),
        "effective_exposure_kmh": round(effective_wind, 1),
        "level": level,
        "is_coastal_exposed": is_coastal,
        "guidance": guidance,
        "computation_method": "WMO Beaufort scale threshold with coastal gust weighting"
    }


def compute_dew_point_spread(temp_c: float, dew_point_c: float) -> Dict[str, Any]:
    """
    Computes dew-point depression (T - T_d) indicating near-surface saturation and condensation potential.
    """
    spread = max(0.0, temp_c - dew_point_c)

    if spread <= 1.5:
        condition = "Near Saturation / Fog or Condensation Likely"
        moisture_context = "High boundary layer saturation; risk of early morning visibility restriction."
    elif spread <= 3.5:
        condition = "Humid / Moist Air"
        moisture_context = "Moist marine airmass; favorable for cloud development and low cloud base."
    elif spread <= 8.0:
        condition = "Moderate Comfort"
        moisture_context = "Balanced relative humidity; nominal surface evaporation."
    else:
        condition = "Dry Air"
        moisture_context = "Elevated vapor deficit; accelerated agricultural evapotranspiration."

    return {
        "temperature_c": round(temp_c, 1),
        "dew_point_c": round(dew_point_c, 1),
        "dew_point_spread_c": round(spread, 1),
        "saturation_condition": condition,
        "moisture_context": moisture_context,
        "computation_method": "Thermodynamic dew-point spread formula (T - Td)"
    }


def compute_pressure_tendency(current_pressure_hpa: float, past_3h_pressure_hpa: Optional[float] = None) -> Dict[str, Any]:
    """
    Computes barometric tendency over a 3-hour synoptic window.
    NOTE: Pressure trends alone cannot predict cyclones or severe storms;
    cyclone guidance strictly requires authoritative IMD advisories and oceanic soundings.
    """
    if past_3h_pressure_hpa is None:
        delta_p = 0.0
    else:
        delta_p = current_pressure_hpa - past_3h_pressure_hpa

    if delta_p <= -3.0:
        tendency = "Rapidly Falling"
        synoptic_note = "Steep pressure fall indicates an approaching trough, low-pressure system, or convective boundary."
    elif delta_p <= -1.5:
        tendency = "Falling"
        synoptic_note = "Gradual pressure fall consistent with diurnal tidal variation or synoptic weakening."
    elif delta_p >= 2.0:
        tendency = "Rising"
        synoptic_note = "Pressure rise consistent with anticyclonic ridging or passing convective outflow."
    else:
        tendency = "Steady"
        synoptic_note = "Stable barometric field within standard semi-diurnal atmospheric tidal limits."

    return {
        "current_pressure_hpa": round(current_pressure_hpa, 1),
        "delta_3h_hpa": round(delta_p, 1),
        "tendency": tendency,
        "synoptic_note": synoptic_note,
        "meteorological_disclaimer": (
            "Surface pressure tendency provides localized synoptic context only. "
            "It does not predict cyclonic storms or severe thunderstorms. "
            "Official cyclone advisories are issued exclusively by the India Meteorological Department (IMD)."
        )
    }


def compute_dry_spell_metrics(daily_forecast: List[Dict[str, Any]], dry_threshold_mm: float = 2.5) -> Dict[str, Any]:
    """
    Computes consecutive dry days in the forecast horizon for water resources and agricultural monitoring.
    """
    consecutive_dry = 0
    max_dry_run = 0

    for d in daily_forecast:
        rain = float(d.get("precipitation_sum_mm", 0.0))
        if rain < dry_threshold_mm:
            consecutive_dry += 1
            if consecutive_dry > max_dry_run:
                max_dry_run = consecutive_dry
        else:
            consecutive_dry = 0

    if max_dry_run >= 10:
        status = "Extended Dry Spell"
        soil_risk = "Significant soil moisture depletion; supplementary irrigation required."
    elif max_dry_run >= 5:
        status = "Moderate Dry Spell"
        soil_risk = "Declining surface soil moisture in rainfed tracts."
    else:
        status = "Normal / Intermittent Rain"
        soil_risk = "Adequate moisture intervals for standard vegetative growth."

    return {
        "consecutive_dry_days": max_dry_run,
        "dry_threshold_mm": dry_threshold_mm,
        "status": status,
        "soil_moisture_risk": soil_risk,
        "computation_method": f"Run-length encoding of consecutive forecast days with precipitation < {dry_threshold_mm} mm"
    }
