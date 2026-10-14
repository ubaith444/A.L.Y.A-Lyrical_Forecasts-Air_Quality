"""
Tamil Nadu Climate & Forecast Intelligence Platform
Operational Intelligence Module 2: Multi-Sector Operational Impact Matrix

Evaluates 7 Key Operational Sectors:
1. Agriculture (Paddy, Sugarcane, Cotton, Groundnut, Tea)
2. Transport & Logistics (Highways, Ghat passes, Freight)
3. Urban Infrastructure (Stormwater drainage, Subways, Low-lying habitations)
4. Water Resources (Reservoir inflows, Evaporative loss, Storage cushions)
5. Coastal Operations (Artisanal fishing, Port logistics, Maritime wave surges)
6. Public Health (Heat index stress, Dehydration, Vulnerable populations)
7. Renewable Energy (Wind power dispatch, Solar irradiance variability)

Transparent Scoring Engine:
R_s = sum(w_{s,i} * x_i)
Decomposed into:
- Hazard Likelihood (H in 0..100)
- District Exposure (E in 0..100)
- Vulnerability & Preparedness (V in 0..100)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.data.districts_data import TAMIL_NADU_DISTRICTS, TN_MAJOR_RESERVOIRS
from backend.services.weather_service import fetch_live_weather, fetch_forecast


# Configured Driver Weights w_{s,i} for normalized variables [0..100]
SECTOR_DRIVER_WEIGHTS = {
    "agriculture": {
        "rain_risk": 0.35,
        "heat_stress": 0.25,
        "dry_spell": 0.25,
        "humidity_excess": 0.15
    },
    "transport_and_logistics": {
        "rain_intensity": 0.40,
        "wind_gusts": 0.30,
        "thermal_strain": 0.15,
        "visibility_deficit": 0.15
    },
    "urban_infrastructure": {
        "accumulated_rain": 0.50,
        "rain_intensity": 0.30,
        "antecedent_moisture": 0.20
    },
    "water_resources": {
        "catchment_inflow": 0.45,
        "dry_spell_duration": 0.35,
        "evaporation_deficit": 0.20
    },
    "coastal_operations": {
        "wind_force": 0.45,
        "squall_gusts": 0.35,
        "coastal_proximity": 0.20
    },
    "public_health": {
        "heat_index": 0.50,
        "nighttime_minimum_temp": 0.30,
        "relative_humidity": 0.20
    },
    "renewable_energy": {
        "wind_velocity": 0.45,
        "cloud_cover_loss": 0.35,
        "thermal_derating": 0.20
    }
}


def score_to_severity(score: float) -> str:
    if score >= 75.0:
        return "Severe"
    elif score >= 50.0:
        return "High"
    elif score >= 25.0:
        return "Moderate"
    return "Low"


def evaluate_district_sector_matrix(district_id: str, horizon_hours: int = 24) -> Dict[str, Any]:
    """
    Evaluates the complete 7-sector impact matrix for a given district over a specified horizon (6, 24, 48, 72h).
    Separates Hazard Likelihood, District Exposure, and Vulnerability/Preparedness.
    """
    d_clean = district_id.lower().strip()
    dist_meta = TAMIL_NADU_DISTRICTS.get(d_clean, TAMIL_NADU_DISTRICTS["chennai"])

    # Live and forecast telemetry
    live = fetch_live_weather(d_clean)
    forecast = fetch_forecast(d_clean, forecast_days=7)

    temp = float(live.get("temperature_2m", 31.0))
    rh = float(live.get("relative_humidity_2m", 68.0))
    rain_now = float(live.get("precipitation_mm", 0.0))
    wind = float(live.get("wind_speed_10m", 14.0))
    gust = float(live.get("wind_gusts_10m", 18.0))
    cloud = float(live.get("cloud_cover", 30.0))
    elev = float(dist_meta.get("elevation_m", 15.0))
    is_coastal = bool(dist_meta.get("is_coastal", False))
    is_hill = elev > 1000.0

    daily = forecast.get("daily", [])
    days_slice = max(1, horizon_hours // 24)
    acc_rain = sum(float(d.get("precipitation_sum_mm", 0.0)) for d in daily[:days_slice])
    max_t = max((float(d.get("temp_max", temp)) for d in daily[:days_slice]), default=temp)

    # Calculate normalized drivers x_i in [0..100]
    norm_rain = min(100.0, (acc_rain / 64.5) * 60.0)
    norm_rain_intensity = min(100.0, (acc_rain / 115.5) * 100.0)
    norm_heat = min(100.0, max(0.0, (max_t - 32.0) / 10.0 * 100.0))
    norm_wind = min(100.0, (wind / 50.0) * 80.0)
    norm_gust = min(100.0, (gust / 70.0) * 100.0)
    norm_dry = 75.0 if acc_rain < 1.0 and max_t > 36.0 else 15.0

    sectors_results = {}

    # 1. Agriculture Sector
    agri_hazard = round(norm_rain * 0.35 + norm_heat * 0.25 + norm_dry * 0.25 + (rh / 100.0 * 20.0), 1)
    agri_exposure = 85.0 if any(c in ["Paddy", "Sugarcane"] for c in dist_meta.get("primary_crops", [])) else 60.0
    agri_vuln = 65.0 if is_hill else (50.0 if not is_coastal else 70.0)
    agri_composite = round(0.50 * agri_hazard + 0.30 * agri_exposure + 0.20 * agri_vuln, 1)

    agri_advisories = []
    if agri_composite >= 50.0:
        agri_advisories.append("Withhold top-dressing nitrogen/urea and pesticide spraying to prevent surface runoff loss.")
        agri_advisories.append("Ensure tertiary field drains are unblocked to prevent standing water stagnation.")
    else:
        agri_advisories.append("Conditions favorable for field intercultural operations and standard irrigation scheduling.")

    sectors_results["agriculture"] = {
        "sector_name": "Agriculture & Crops",
        "meteorological_drivers": f"Rainfall: {acc_rain:.1f} mm, Max Temp: {max_t:.1f} °C, RH: {rh:.0f}%",
        "potential_operational_impact": "Sowing disruption, vegetative water stress, and fertilizer wash-off" if agri_composite >= 50 else "Nominal crop vegetative growth",
        "recommended_guidance": " ".join(agri_advisories),
        "hazard_likelihood": agri_hazard,
        "exposure_score": agri_exposure,
        "vulnerability_score": agri_vuln,
        "composite_score": agri_composite,
        "severity": score_to_severity(agri_composite),
        "primary_assets_monitored": dist_meta.get("primary_crops", ["Paddy", "Groundnut"])
    }

    # 2. Transport & Logistics Sector
    trans_hazard = round(norm_rain_intensity * 0.40 + norm_gust * 0.30 + norm_heat * 0.15 + 15.0, 1)
    trans_exposure = 90.0 if d_clean in ["chennai", "coimbatore", "tiruchirappalli", "madurai"] else 60.0
    trans_vuln = 85.0 if is_hill else 45.0
    trans_composite = round(0.50 * trans_hazard + 0.30 * trans_exposure + 0.20 * trans_vuln, 1)

    trans_guidance = (
        "Ghat sections vulnerable to rock-falls and lane subsidence; restrict nocturnal heavy freight."
        if is_hill and acc_rain > 35.0
        else ("Monitor arterial highways and low-lying railway underpasses for water accumulation." if acc_rain > 30.0 else "Standard transit operations across arterial road corridors.")
    )

    sectors_results["transport_and_logistics"] = {
        "sector_name": "Transport & Logistics",
        "meteorological_drivers": f"Precip Intensity: {acc_rain:.1f} mm, Gusts: {gust:.1f} km/h",
        "potential_operational_impact": "Transit delays, reduced highway speed, and localized road disruption" if trans_composite >= 50 else "Nominal traffic flow across highway network",
        "recommended_guidance": trans_guidance,
        "hazard_likelihood": trans_hazard,
        "exposure_score": trans_exposure,
        "vulnerability_score": trans_vuln,
        "composite_score": trans_composite,
        "severity": score_to_severity(trans_composite),
        "primary_assets_monitored": ["National/State Highways", "Freight Corridors", "Ghat Passes" if is_hill else "Urban Arterials"]
    }

    # 3. Urban Infrastructure Sector
    urban_hazard = round(norm_rain_intensity * 0.50 + norm_rain * 0.30 + 15.0, 1)
    urban_exposure = 95.0 if d_clean in ["chennai", "coimbatore", "madurai", "salem"] else 40.0
    urban_vuln = 75.0 if is_coastal else 50.0
    urban_composite = round(0.50 * urban_hazard + 0.30 * urban_exposure + 0.20 * urban_vuln, 1)

    urban_guidance = (
        "Deploy mobile de-watering pumps at identified subway inundation spots; clear stormwater canal gates."
        if urban_composite >= 50.0
        else "Routine municipal stormwater drainage monitoring."
    )

    sectors_results["urban_infrastructure"] = {
        "sector_name": "Urban Infrastructure",
        "meteorological_drivers": f"Accumulated Rain: {acc_rain:.1f} mm, Intensity: {norm_rain_intensity:.0f}%",
        "potential_operational_impact": "Localized waterlogging, stormwater surcharge, and traffic slowing" if urban_composite >= 50 else "Normal municipal infrastructure functioning",
        "recommended_guidance": urban_guidance,
        "hazard_likelihood": urban_hazard,
        "exposure_score": urban_exposure,
        "vulnerability_score": urban_vuln,
        "composite_score": urban_composite,
        "severity": score_to_severity(urban_composite),
        "primary_assets_monitored": ["Stormwater Canals", "Vehicular Subways", "Low-Lying Urban Basins"]
    }

    # 4. Water Resources & Reservoirs
    res_list = dist_meta.get("critical_reservoirs", ["District Tanks & Ponds"])
    water_hazard = round(norm_rain * 0.45 + (100.0 - norm_rain if norm_dry > 50 else 20.0) * 0.35 + 15.0, 1)
    water_exposure = 80.0 if res_list else 50.0
    water_vuln = 60.0
    water_composite = round(0.50 * water_hazard + 0.30 * water_exposure + 0.20 * water_vuln, 1)

    water_guidance = (
        f"Significant catchment runoff into {', '.join(res_list)}; inspect spillway gates and downstream bunds."
        if acc_rain >= 50.0
        else f"Maintain planned releases from {', '.join(res_list)}; balanced seasonal storage replenishment."
    )

    sectors_results["water_resources"] = {
        "sector_name": "Water Resources",
        "meteorological_drivers": f"Catchment Rainfall: {acc_rain:.1f} mm, Dry Score: {norm_dry:.0f}",
        "potential_operational_impact": "Inflow surge into reservoirs or evaporation-driven storage drawdowns" if water_composite >= 50 else "Equilibrium between domestic drawdowns and surface inflow",
        "recommended_guidance": water_guidance,
        "hazard_likelihood": water_hazard,
        "exposure_score": water_exposure,
        "vulnerability_score": water_vuln,
        "composite_score": water_composite,
        "severity": score_to_severity(water_composite),
        "primary_assets_monitored": res_list
    }

    # 5. Coastal Operations
    coastal_hazard = round(norm_wind * 0.45 + norm_gust * 0.35 + (20.0 if is_coastal else 0.0), 1) if is_coastal else 10.0
    coastal_exposure = 90.0 if is_coastal else 0.0
    coastal_vuln = 80.0 if is_coastal else 0.0
    coastal_composite = round(0.50 * coastal_hazard + 0.30 * coastal_exposure + 0.20 * coastal_vuln, 1) if is_coastal else 10.0

    coastal_guidance = (
        "Squally sea conditions; artisanal fishermen advised not to venture into maritime areas. Port operations on alert."
        if is_coastal and gust >= 45.0
        else ("Standard coastal port loading and coastal fishing permitted." if is_coastal else "Not applicable (Inland District).")
    )

    sectors_results["coastal_operations"] = {
        "sector_name": "Coastal Operations",
        "meteorological_drivers": f"Wind: {wind:.1f} km/h, Gusts: {gust:.1f} km/h (Coastal: {is_coastal})",
        "potential_operational_impact": "Rough sea states, port berth delays, and small craft marine warnings" if coastal_composite >= 50 else "Safe maritime conditions and regular coastal shipping",
        "recommended_guidance": coastal_guidance,
        "hazard_likelihood": coastal_hazard,
        "exposure_score": coastal_exposure,
        "vulnerability_score": coastal_vuln,
        "composite_score": coastal_composite,
        "severity": score_to_severity(coastal_composite),
        "primary_assets_monitored": ["Major/Minor Ports", "Fishing Harbors", "Coastal Highway Corridors"]
    }

    # 6. Public Health Sector
    heat_idx = temp + 2.5 if rh > 50 else temp
    health_hazard = round(min(100.0, max(15.0, (heat_idx - 28.0) / 14.0 * 100.0)), 1)
    health_exposure = 85.0 if d_clean in ["chennai", "madurai", "salem", "tirunelveli"] else 60.0
    health_vuln = 65.0
    health_composite = round(0.50 * health_hazard + 0.30 * health_exposure + 0.20 * health_vuln, 1)

    health_guidance = (
        "High thermal strain; issue public hydration advisories and reschedule strenuous outdoor afternoon labor."
        if health_composite >= 50.0
        else "Nominal ambient thermal environment with low heat exhaustion risk."
    )

    sectors_results["public_health"] = {
        "sector_name": "Public Health",
        "meteorological_drivers": f"Ambient: {temp:.1f} °C, RH: {rh:.0f}%, Heat Index Proxy: {heat_idx:.1f} °C",
        "potential_operational_impact": "Dehydration, heat cramps, and increased health clinic footfall" if health_composite >= 50 else "Low community environmental health risk",
        "recommended_guidance": health_guidance,
        "hazard_likelihood": health_hazard,
        "exposure_score": health_exposure,
        "vulnerability_score": health_vuln,
        "composite_score": health_composite,
        "severity": score_to_severity(health_composite),
        "primary_assets_monitored": ["Outdoor Labor Workforces", "Urban Elderly Populations", "Primary Health Centers"]
    }

    # 7. Renewable Energy Sector
    wind_gen_score = min(100.0, (wind / 35.0) * 100.0)
    solar_derate_score = min(100.0, (cloud / 80.0) * 100.0)
    re_hazard = round(abs(wind_gen_score - 50.0) * 0.8 + solar_derate_score * 0.4, 1)
    re_exposure = 85.0 if d_clean in ["tirunelveli", "coimbatore", "kanyakumari", "ramanathapuram"] else 40.0
    re_vuln = 50.0
    re_composite = round(0.50 * re_hazard + 0.30 * re_exposure + 0.20 * re_vuln, 1)

    re_guidance = (
        "Significant solar generation dip expected due to cloud cover; schedule balancing reserves."
        if cloud > 60.0
        else ("High wind generation window in mountain gap corridors; optimize transmission evacuation." if wind > 20.0 else "Stable baseline solar and wind output.")
    )

    sectors_results["renewable_energy"] = {
        "sector_name": "Renewable Energy",
        "meteorological_drivers": f"Cloud Cover: {cloud:.0f}%, Wind Speed: {wind:.1f} km/h",
        "potential_operational_impact": "Solar irradiance variability and wind dispatch fluctuations" if re_composite >= 50 else "Predictable renewable generation profile",
        "recommended_guidance": re_guidance,
        "hazard_likelihood": re_hazard,
        "exposure_score": re_exposure,
        "vulnerability_score": re_vuln,
        "composite_score": re_composite,
        "severity": score_to_severity(re_composite),
        "primary_assets_monitored": ["Wind Farms (Ghat passes)", "Solar Photovoltaic Parks", "TANGEDCO Sub-stations"]
    }

    return {
        "district_id": d_clean,
        "district_name": dist_meta["name"],
        "tamil_name": dist_meta.get("tamil_name", ""),
        "region": dist_meta.get("region", "Tamil Nadu"),
        "forecast_horizon_hours": horizon_hours,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "sectors": sectors_results
    }


from concurrent.futures import ThreadPoolExecutor, as_completed


def get_all_districts_sector_matrix(
    sector_filter: Optional[str] = None,
    horizon_hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Evaluates multi-sector impact across all 38 districts for state-level ranking and map layers.
    Uses concurrent ThreadPoolExecutor for high-performance throughput.
    """
    district_ids = list(TAMIL_NADU_DISTRICTS.keys())
    results_map = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_id = {
            executor.submit(evaluate_district_sector_matrix, d_id, horizon_hours): d_id
            for d_id in district_ids
        }
        for future in as_completed(future_to_id):
            d_id = future_to_id[future]
            try:
                eval_res = future.result()
                if sector_filter and sector_filter.lower() in eval_res["sectors"]:
                    eval_res["highlighted_sector"] = eval_res["sectors"][sector_filter.lower()]
                results_map[d_id] = eval_res
            except Exception as e:
                # Fallback record if an individual district evaluation encountered an error
                dist_meta = TAMIL_NADU_DISTRICTS[d_id]
                results_map[d_id] = {
                    "district_id": d_id,
                    "district_name": dist_meta["name"],
                    "tamil_name": dist_meta.get("tamil_name", ""),
                    "region": dist_meta.get("region", "Tamil Nadu"),
                    "forecast_horizon_hours": horizon_hours,
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                    "sectors": {},
                    "error": str(e)
                }

    # Maintain deterministic district ordering
    return [results_map[d_id] for d_id in district_ids if d_id in results_map]
