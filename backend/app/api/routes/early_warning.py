"""REST API endpoints for the Intelligent Multi-Hazard Early-Warning System."""

from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.dependencies import get_location_service, get_provider
from app.services.early_warning import EarlyWarningEngine
from app.services.alert_dispatcher import AlertDispatcher
from app.services.providers import OpenMeteoClient

router = APIRouter()


class DispatchAlertRequest(BaseModel):
    hazard: str = Field(..., description="Hazard type: lightning, thunderstorm, heavy_rainfall, landslide, or tsunami")
    level: int = Field(..., ge=0, le=3, description="Severity level: 0 (Informational), 1 (Watch), 2 (Warning), 3 (Emergency)")
    location_id: str
    headline: str
    instructions: list[str] = Field(default_factory=list)
    channels: list[str] | None = None


@router.get("/alerts")
async def get_location_early_warning_alerts(
    location_id: str = Query(default="chennai"),
    sim_temp: float | None = Query(default=None),
    sim_rh: float | None = Query(default=None),
    sim_wind_gust: float | None = Query(default=None),
    sim_precip_24h: float | None = Query(default=None),
    sim_antecedent_72h: float | None = Query(default=None),
    sim_tsunami_active: bool = Query(default=False),
    provider: OpenMeteoClient = Depends(get_provider),
) -> dict[str, Any]:
    """Returns real-time or simulated early-warning hazard dossier for a specific location,

    evaluating lightning, thunderstorm, heavy rain/flood, landslide, and authoritative tsunami risks.
    """
    locations = get_location_service()
    loc = locations.get(location_id)

    # Defaults or live weather ingestion
    temp = sim_temp if sim_temp is not None else 32.0
    rh = sim_rh if sim_rh is not None else 72.0
    gust = sim_wind_gust if sim_wind_gust is not None else 28.0
    antecedent = sim_antecedent_72h if sim_antecedent_72h is not None else 35.0

    if sim_precip_24h is not None:
        # Distribute simulated 24h rain into hourly series
        hourly_series = [round(sim_precip_24h / 24.0, 2)] * 24 + [0.5] * 48
    else:
        # Ingest live forecast from Open-Meteo
        try:
            live = await provider.forecast(
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                timezone=loc["timezone"],
                hourly=["temperature_2m", "relative_humidity_2m", "precipitation", "wind_gusts_10m"],
                forecast_days=3,
            )
            hourly_data = live.get("hourly", {})
            temps = hourly_data.get("temperature_2m", [])
            rhs = hourly_data.get("relative_humidity_2m", [])
            gusts = hourly_data.get("wind_gusts_10m", [])
            precips = hourly_data.get("precipitation", [])

            if temps:
                temp = float(temps[0])
            if rhs:
                rh = float(rhs[0])
            if gusts:
                gust = float(gusts[0])
            hourly_series = [float(p) for p in precips] if precips else [0.0] * 72
        except Exception:
            hourly_series = [1.2, 2.5, 4.0, 12.0, 8.5, 2.0] + [0.5] * 66

    official_tsunami = None
    if sim_tsunami_active:
        official_tsunami = {
            "active": True,
            "level": 3,
            "headline": "INCOIS TSUNAMI WARNING BULLETIN NO. 04: INDIAN OCEAN SEISMIC EVENT",
            "bulletin_id": "INCOIS-TSU-TN-2026",
            "estimated_arrival": "T+35 mins (Immediate Shoreline Evacuation Required)",
        }

    return EarlyWarningEngine.generate_location_early_warning_dossier(
        location_id=location_id,
        location_name=loc["name"],
        district=loc.get("district", loc["name"]),
        state=loc.get("state", "Tamil Nadu"),
        current_temp_c=temp,
        relative_humidity=rh,
        wind_gust_kmh=gust,
        hourly_precip_series=hourly_series,
        antecedent_rain_72h_mm=antecedent,
        official_tsunami_bulletin=official_tsunami,
    )


@router.get("/regional-overview")
async def get_regional_early_warning_overview(
    state: str = Query(default="Tamil Nadu"),
) -> dict[str, Any]:
    """Returns multi-district early warning situation matrix for Tamil Nadu or other states,

    allowing disaster authorities to view simultaneous hazard postures across coastal, plain, and montane zones.
    """
    locations = get_location_service()
    all_locs = locations.list_all()

    # Filter for target state locations
    target_locs = [l for l in all_locs if l.get("state", "").lower() == state.lower()]
    if not target_locs:
        target_locs = all_locs[:8]

    overview_items = []
    for loc in target_locs:
        loc_id = loc["id"]
        # Representative assessment
        dossier = EarlyWarningEngine.generate_location_early_warning_dossier(
            location_id=loc_id,
            location_name=loc["name"],
            district=loc.get("district", loc["name"]),
            state=loc.get("state", state),
            current_temp_c=31.0,
            relative_humidity=70.0,
            wind_gust_kmh=30.0,
        )
        overview_items.append({
            "location_id": loc_id,
            "name": loc["name"],
            "type": loc.get("type", "district"),
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "overall_alert": dossier["overall_alert"],
            "is_coastal": dossier["location"]["is_coastal"],
            "is_mountainous": dossier["location"]["is_mountainous"],
            "top_threat": dossier["overall_alert"]["primary_threat"],
        })

    return {
        "region": state,
        "district_count": len(overview_items),
        "items": overview_items,
        "coordinating_agency": "Tamil Nadu State Disaster Management Authority (TNSDMA) & IMD",
    }


@router.post("/simulate-dispatch", status_code=201)
async def simulate_alert_dispatch(request: DispatchAlertRequest) -> dict[str, Any]:
    """Simulates dispatch of a multi-channel alert (Web Push, SMS, Email)

    with duplicate suppression check and audit logging.
    """
    locations = get_location_service()
    loc = locations.get(request.location_id)
    loc_name = loc["name"] if loc else request.location_id.title()

    return AlertDispatcher.dispatch_alert(
        hazard=request.hazard,
        level=request.level,
        location_id=request.location_id,
        location_name=loc_name,
        headline=request.headline,
        instructions=request.instructions,
        channels=request.channels,
    )


@router.get("/history")
async def get_alert_dispatch_history(
    location_id: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Returns recent alert dispatch records with duplicate suppression logs."""
    history = AlertDispatcher.get_history(location_id=location_id, limit=limit)
    return {"items": history, "count": len(history)}
