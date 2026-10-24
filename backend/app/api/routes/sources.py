from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def data_sources() -> dict:
    return {
        "items": [
            {
                "id": "open-meteo-forecast",
                "name": "Open-Meteo Forecast API",
                "kind": "model_forecast",
                "url": "https://open-meteo.com/en/docs",
                "limitations": "Forecast grid-cell values, not guaranteed station observations.",
            },
            {
                "id": "open-meteo-air-quality",
                "name": "Open-Meteo Air Quality API",
                "kind": "modelled_air_quality",
                "url": "https://open-meteo.com/en/docs/air-quality-api",
                "limitations": "US and European AQI values are provider-derived; not Indian AQI.",
            },
            {
                "id": "open-meteo-archive",
                "name": "Open-Meteo Historical Weather API",
                "kind": "reanalysis",
                "url": "https://open-meteo.com/en/docs/historical-weather-api",
                "limitations": "ERA5 reanalysis, not direct weather-station observations.",
            },
        ]
    }
