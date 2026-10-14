"""
Tamil Nadu Climate & Forecast Intelligence Platform
Phase 1A: Multi-Sector Impact & Risk Monitoring Engine

Translates meteorological variables into 4 operational decision vectors:
1. Agriculture & Crops (Paddy Samba/Kuruvai, Sugarcane, Cotton, Nilgiris Tea)
2. Water Resources & Reservoirs (Catchment Inflow, Reservoir Spill, Storage Stress)
3. Urban & Transport Systems (Waterlogging hotspots, Ghat road landslides, Coastal surge)
4. Public Health (Heat Index, Wet-Bulb Stress, Vector-borne dampness)

Also computes the statewide 38-district Risk Matrix.
"""

from typing import Dict, Any, List
from backend.data.districts_data import TAMIL_NADU_DISTRICTS, TN_MAJOR_RESERVOIRS
from backend.services.weather_service import fetch_live_weather, get_location_coordinates


def evaluate_sector_impacts(
    district_id: str,
    live_data: Dict[str, Any],
    forecast_data: Dict[str, Any],
    ml_prediction: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates multi-sector impact for a specific district based on live conditions,
    upcoming 7-day forecast, and ML probability.
    """
    dist_info = TAMIL_NADU_DISTRICTS.get(district_id.lower(), TAMIL_NADU_DISTRICTS["chennai"])
    
    # Extract operational parameters
    temp = float(live_data.get("temperature_2m", 30.0))
    rh = float(live_data.get("relative_humidity_2m", 65.0))
    rain_now = float(live_data.get("precipitation_mm", 0.0))
    wind = float(live_data.get("wind_speed_10m", 12.0))
    wind_gust = float(live_data.get("wind_gusts_10m", 16.0))
    elev = float(dist_info.get("elevation_m", 10.0))
    is_coastal = bool(dist_info.get("is_coastal", False))
    is_hill = elev > 1000

    # 3-day projected rainfall
    daily_forecasts = forecast_data.get("daily", [])
    rain_3day_sum = sum(d.get("precipitation_sum_mm", 0.0) for d in daily_forecasts[:3])
    max_forecast_temp = max((d.get("temp_max", 32.0) for d in daily_forecasts[:3]), default=32.0)
    ml_rain_mm = ml_prediction.get("predictions", {}).get("predicted_rain_depth_mm", 0.0)

    effective_rain_risk = max(rain_3day_sum, ml_rain_mm * 1.5)

    # 1. Agriculture & Crops Sector
    crops = dist_info.get("primary_crops", ["Paddy", "Sugarcane"])
    agri_advisories = []
    
    if effective_rain_risk > 60.0:
        agri_level = "Severe"
        agri_advisories.append("High risk of water inundation in low-lying paddy nurseries and standing Samba crops.")
        agri_advisories.append("Immediately withhold nitrogen/urea top-dressing and pesticide spraying to prevent wash-off.")
        agri_advisories.append("Ensure drainage channels and field bund trenches are cleared to release excess surface runoff.")
    elif effective_rain_risk > 25.0:
        agri_level = "Warning"
        agri_advisories.append("Moderate to heavy rainfall expected. Postpone harvesting of groundnut and pulses by 48-72 hours.")
        agri_advisories.append("Suspend planned chemical fertilizer broadcast; monitor banana and sugarcane crops for wind lodging.")
    elif max_forecast_temp >= 38.0 and effective_rain_risk < 2.0:
        agri_level = "Advisory"
        agri_advisories.append("High evapotranspiration stress. Provide light and frequent irrigation during evening hours.")
        agri_advisories.append("Apply mulching in orchards and vegetable plots to conserve soil moisture.")
    else:
        agri_level = "Normal"
        agri_advisories.append("Favorable weather conditions for field tilling, intercultural operations, and standard irrigation.")

    # 2. Water Resources & Reservoirs Sector
    reservoirs = dist_info.get("critical_reservoirs", ["District Tanks & Ponds"])
    water_advisories = []

    if effective_rain_risk > 75.0 or (is_hill and effective_rain_risk > 45.0):
        water_level = "Severe"
        water_advisories.append(f"Substantial catchment runoff anticipated into {', '.join(reservoirs)}.")
        water_advisories.append("Reservoir authorities should maintain flood cushion and monitor spillway outflow readiness.")
        water_advisories.append("Low-lying riparian communities downstream should prepare for sudden river discharge surges.")
    elif effective_rain_risk > 30.0:
        water_level = "Warning"
        water_advisories.append(f"Beneficial catchment inflows expected into {', '.join(reservoirs)}.")
        water_advisories.append("Recommended to capture runoff in secondary percolation ponds and village irrigation tanks.")
    elif effective_rain_risk < 5.0 and temp > 36.0:
        water_level = "Advisory"
        water_advisories.append("Elevated evaporation loss from open water bodies; prioritize domestic supply over canal releases.")
    else:
        water_level = "Normal"
        water_advisories.append("Steady storage levels with balanced recharge and planned agricultural drawdowns.")

    # 3. Transport & Urban Infrastructure
    transport_advisories = []
    if is_hill and effective_rain_risk > 40.0:
        transport_level = "Severe"
        transport_advisories.append("High vulnerability to landslides, rock-falls, and road subsidence along ghat hairpin bends.")
        transport_advisories.append("Restrict heavy tourist vehicles and nighttime transit along hill corridors.")
    elif is_coastal and (effective_rain_risk > 60.0 or wind_gust > 50.0):
        transport_level = "Warning"
        transport_advisories.append("East Coast Road (ECR) and arterial urban subways vulnerable to water stagnation.")
        transport_advisories.append("Fishermen advised not to venture into squally coastal sea; wind gusts up to 55 km/h.")
    elif effective_rain_risk > 35.0:
        transport_level = "Advisory"
        transport_advisories.append("Localized urban flash waterlogging at railway underpasses and ring road junctions.")
        transport_advisories.append("Motorists should anticipate reduced visibility and slick road tarmac.")
    else:
        transport_level = "Normal"
        transport_advisories.append("Clear transit conditions across national and state highways with optimal visibility.")

    # 4. Public Health & Heat Index
    health_advisories = []
    # Heat index simplified formula
    heat_index = temp + 0.5555 * ((rh / 100.0) * 6.11 * (2.71828 ** (5417.7530 * (1/273.16 - 1/(273.15 + temp)))) - 10.0)
    
    if heat_index >= 41.0 or temp >= 40.0:
        health_level = "Severe"
        health_advisories.append("Extreme heat stress hazard. High probability of heat exhaustion or heat stroke upon prolonged exposure.")
        health_advisories.append("Direct sun exposure between 11:30 AM and 3:30 PM strongly discouraged for construction and field workers.")
        health_advisories.append("Maintain aggressive oral hydration (ORS, buttermilk, tender coconut water).")
    elif heat_index >= 35.0:
        health_level = "Warning"
        health_advisories.append("Uncomfortable humid heat. Elderly and outdoor laborers should take frequent shaded breaks.")
    elif rain_now > 5.0 and rh > 80.0:
        health_level = "Advisory"
        health_advisories.append("Elevated ambient dampness increases risk of post-rain mosquito breeding and waterborne vectors.")
        health_advisories.append("Eliminate stagnant water around residential premises and boil drinking water.")
    else:
        health_level = "Normal"
        health_advisories.append("Comfortable ambient bioclimatic conditions with minimal physiological thermal strain.")

    return {
        "district_id": district_id.lower(),
        "district_name": dist_info["name"],
        "evaluated_at": live_data.get("timestamp"),
        "agriculture": {
            "risk_level": agri_level,
            "monitored_crops": crops,
            "advisories": agri_advisories
        },
        "water_resources": {
            "risk_level": water_level,
            "monitored_reservoirs": reservoirs,
            "advisories": water_advisories
        },
        "transport_and_urban": {
            "risk_level": transport_level,
            "advisories": transport_advisories
        },
        "public_health": {
            "risk_level": health_level,
            "heat_index_celsius": round(heat_index, 1),
            "advisories": health_advisories
        }
    }


def get_statewide_risk_matrix() -> List[Dict[str, Any]]:
    """
    Computes a risk index for all 38 districts across Tamil Nadu:
    - Heavy Rainfall Risk
    - Extreme Heat Risk
    - Flash Flood / Landslide Risk
    - Dry Spell / Drought Risk
    """
    results = []
    for dist_id, dist in TAMIL_NADU_DISTRICTS.items():
        is_coastal = dist["is_coastal"]
        elev = dist["elevation_m"]
        is_hill = elev > 1000

        # Base risks tailored to district geography
        if is_hill:
            rain_risk = "Advisory"
            flood_risk = "Warning" # landslides
            heat_risk = "Normal"
            drought_risk = "Normal"
            overall_severity = "Warning"
        elif is_coastal:
            rain_risk = "Advisory"
            flood_risk = "Advisory" # urban waterlogging
            heat_risk = "Advisory" # humidity
            drought_risk = "Normal"
            overall_severity = "Advisory"
        elif dist_id in ("karur", "dharmapuri", "tiruchirappalli", "madurai"):
            rain_risk = "Normal"
            flood_risk = "Normal"
            heat_risk = "Warning"
            drought_risk = "Advisory"
            overall_severity = "Warning"
        else:
            rain_risk = "Normal"
            flood_risk = "Normal"
            heat_risk = "Normal"
            drought_risk = "Normal"
            overall_severity = "Normal"

        results.append({
            "district_id": dist_id,
            "district_name": dist["name"],
            "tamil_name": dist.get("tamil_name", ""),
            "region": "Western Ghats" if is_hill else ("Coastal Corridor" if is_coastal else "Interior Plains"),
            "overall_severity": overall_severity,
            "heavy_rain_alert": rain_risk,
            "heat_stress_alert": heat_risk,
            "flood_landslide_alert": flood_risk,
            "drought_stress_alert": drought_risk
        })

    return results
