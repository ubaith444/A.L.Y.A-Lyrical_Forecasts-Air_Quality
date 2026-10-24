from typing import Any

# CPCB Breakpoints: list of tuples (B_low, B_high, I_low, I_high)
# Concentrations for PM2.5, PM10, NO2, SO2, O3 are in µg/m³; CO is in mg/m³
CPCB_BREAKPOINTS: dict[str, list[tuple[float, float, float, float]]] = {
    "pm2_5": [
        (0.0, 30.0, 0.0, 50.0),
        (30.1, 60.0, 51.0, 100.0),
        (60.1, 90.0, 101.0, 200.0),
        (90.1, 120.0, 201.0, 300.0),
        (120.1, 250.0, 301.0, 400.0),
        (250.1, 380.0, 401.0, 500.0),
    ],
    "pm10": [
        (0.0, 50.0, 0.0, 50.0),
        (51.0, 100.0, 51.0, 100.0),
        (101.0, 250.0, 101.0, 200.0),
        (251.0, 350.0, 201.0, 300.0),
        (351.0, 430.0, 301.0, 400.0),
        (431.0, 510.0, 401.0, 500.0),
    ],
    "nitrogen_dioxide": [
        (0.0, 40.0, 0.0, 50.0),
        (41.0, 80.0, 51.0, 100.0),
        (81.0, 180.0, 101.0, 200.0),
        (181.0, 280.0, 201.0, 300.0),
        (281.0, 400.0, 301.0, 400.0),
        (401.0, 500.0, 401.0, 500.0),
    ],
    "sulphur_dioxide": [
        (0.0, 40.0, 0.0, 50.0),
        (41.0, 80.0, 51.0, 100.0),
        (81.0, 380.0, 101.0, 200.0),
        (381.0, 800.0, 201.0, 300.0),
        (801.0, 1600.0, 301.0, 400.0),
        (1601.0, 2000.0, 401.0, 500.0),
    ],
    "carbon_monoxide": [
        (0.0, 1.0, 0.0, 50.0),
        (1.01, 2.0, 51.0, 100.0),
        (2.01, 10.0, 101.0, 200.0),
        (10.01, 17.0, 201.0, 300.0),
        (17.01, 34.0, 301.0, 400.0),
        (34.01, 50.0, 401.0, 500.0),
    ],
    "ozone": [
        (0.0, 50.0, 0.0, 50.0),
        (51.0, 100.0, 51.0, 100.0),
        (101.0, 168.0, 101.0, 200.0),
        (169.0, 208.0, 201.0, 300.0),
        (209.0, 748.0, 301.0, 400.0),
        (749.0, 1000.0, 401.0, 500.0),
    ],
}

CPCB_CATEGORIES = [
    (50, "Good", "Minimal health impact."),
    (100, "Satisfactory", "Minor breathing discomfort to sensitive people."),
    (200, "Moderate", "Breathing discomfort to people with asthma, lung, and heart diseases."),
    (300, "Poor", "Breathing discomfort to most people on prolonged exposure."),
    (400, "Very Poor", "Respiratory illness to the people on prolonged exposure."),
    (500, "Severe", "Affects healthy people and seriously impacts those with existing diseases."),
]


def calculate_sub_index(pollutant: str, concentration: float) -> float | None:
    """Calculate individual pollutant sub-index based on CPCB linear interpolation formula."""
    if concentration < 0:
        return None
    breakpoints = CPCB_BREAKPOINTS.get(pollutant)
    if not breakpoints:
        return None

    # Check bounds
    for b_low, b_high, i_low, i_high in breakpoints:
        if b_low <= concentration <= b_high:
            # Linear interpolation formula
            return i_low + ((i_high - i_low) / (b_high - b_low)) * (concentration - b_low)

    # Beyond upper breakpoint
    last = breakpoints[-1]
    if concentration > last[1]:
        return 500.0
    return None


def get_cpcb_category_and_guidance(aqi: float) -> tuple[str, str]:
    """Map numeric CPCB AQI to official category and deterministic health guidance."""
    for upper, category, guidance in CPCB_CATEGORIES:
        if aqi <= upper:
            return category, guidance
    return "Severe", "Affects healthy people and seriously impacts those with existing diseases."


def compute_indian_aqi(hourly_data: dict[str, list[Any]] | None) -> dict[str, Any]:
    """
    Computes official CPCB Indian National Air Quality Index (NAQI).

    Rules enforced:
    1. Averaging periods: 24h for PM2.5, PM10, NO2, SO2; 8h for CO, O3.
    2. Data completeness: at least 16 hours for 24h average; at least 6 hours for 8h average.
    3. Minimum pollutants: at least 3 pollutants with valid averages, including at least one of PM2.5 or PM10.
    4. AQI = max(sub-indices); dominant pollutant = pollutant with max sub-index.
    """
    if not isinstance(hourly_data, dict):
        return {
            "value": None,
            "category": "Unavailable",
            "standard": "Indian CPCB National Air Quality Index (NAQI)",
            "dominant_pollutant": None,
            "sub_indices": {},
            "status": "unavailable",
            "reason": "No hourly time-series data available to compute required 24-hour and 8-hour averages.",
        }

    # Extract valid hourly readings (taking the most recent 24 hours of available data)
    pollutant_averages: dict[str, float] = {}

    # 24-hour pollutants
    for pol in ["pm2_5", "pm10", "nitrogen_dioxide", "sulphur_dioxide"]:
        series = hourly_data.get(pol)
        if isinstance(series, list) and series:
            recent_24 = [v for v in series[-24:] if isinstance(v, (int, float)) and not isinstance(v, bool)]
            # Need at least 16 hours (66.7%) for valid 24-hr average
            if len(recent_24) >= 16:
                pollutant_averages[pol] = sum(recent_24) / len(recent_24)

    # 8-hour pollutants
    # Note: Open-Meteo returns CO in µg/m³, but CPCB formula requires mg/m³
    co_series = hourly_data.get("carbon_monoxide")
    if isinstance(co_series, list) and co_series:
        recent_8_co = [v for v in co_series[-8:] if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(recent_8_co) >= 6:
            # Convert µg/m³ to mg/m³
            avg_ug = sum(recent_8_co) / len(recent_8_co)
            pollutant_averages["carbon_monoxide"] = avg_ug / 1000.0

    o3_series = hourly_data.get("ozone")
    if isinstance(o3_series, list) and o3_series:
        recent_8_o3 = [v for v in o3_series[-8:] if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if len(recent_8_o3) >= 6:
            pollutant_averages["ozone"] = sum(recent_8_o3) / len(recent_8_o3)

    # CPCB Minimum criteria check:
    # 1. At least one particulate matter pollutant (PM2.5 or PM10)
    has_particulate = "pm2_5" in pollutant_averages or "pm10" in pollutant_averages
    # 2. At least 3 pollutants total
    pollutant_count = len(pollutant_averages)

    if not has_particulate:
        return {
            "value": None,
            "category": "Unavailable",
            "standard": "Indian CPCB National Air Quality Index (NAQI)",
            "dominant_pollutant": None,
            "sub_indices": {},
            "status": "unavailable",
            "reason": "CPCB criteria requires at least one particulate matter measurement (PM2.5 or PM10).",
        }

    if pollutant_count < 3:
        return {
            "value": None,
            "category": "Unavailable",
            "standard": "Indian CPCB National Air Quality Index (NAQI)",
            "dominant_pollutant": None,
            "sub_indices": {},
            "status": "unavailable",
            "reason": f"CPCB criteria requires at least 3 monitored pollutants with valid averaging periods; found {pollutant_count}.",
        }

    # Calculate sub-indices
    sub_indices: dict[str, float] = {}
    for pol, avg in pollutant_averages.items():
        sub = calculate_sub_index(pol, avg)
        if sub is not None:
            sub_indices[pol] = round(sub, 1)

    if not sub_indices:
        return {
            "value": None,
            "category": "Unavailable",
            "standard": "Indian CPCB National Air Quality Index (NAQI)",
            "dominant_pollutant": None,
            "sub_indices": {},
            "status": "unavailable",
            "reason": "Unable to calculate pollutant sub-indices from concentration values.",
        }

    max_sub = max(sub_indices.values())
    dominant_pollutant = max(sub_indices, key=sub_indices.get)  # type: ignore[arg-type]
    overall_aqi = int(round(max_sub))
    category, guidance = get_cpcb_category_and_guidance(overall_aqi)

    return {
        "value": overall_aqi,
        "category": category,
        "standard": "Indian CPCB National Air Quality Index (NAQI)",
        "dominant_pollutant": dominant_pollutant,
        "sub_indices": sub_indices,
        "averages_used": {k: round(v, 2) for k, v in pollutant_averages.items()},
        "health_guidance": guidance,
        "status": "calculated",
        "method": "Official CPCB NAQI linear interpolation with 24h/8h averaging periods.",
    }
