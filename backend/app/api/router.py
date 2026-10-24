from fastapi import APIRouter

from app.api.routes import (
    advanced_ml,
    air_quality,
    early_warning,
    evaluation,
    health,
    historical,
    live_monitor,
    locations,
    ml,
    sources,
    weather,
)

api_router = APIRouter()
api_router.include_router(live_monitor.router, prefix="/live-monitor", tags=["Live Location Monitor"])
api_router.include_router(early_warning.router, prefix="/early-warning", tags=["Early Warning & Disaster Alerts"])
api_router.include_router(health.router, tags=["System"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(
    air_quality.router, prefix="/air-quality", tags=["Air quality"]
)
api_router.include_router(
    historical.router, prefix="/historical", tags=["Historical analytics"]
)
api_router.include_router(
    ml.router, prefix="/ml", tags=["Machine Learning Forecasting"]
)
api_router.include_router(
    evaluation.router, prefix="/evaluations", tags=["Forecast evaluation"]
)
api_router.include_router(
    advanced_ml.router, prefix="/advanced-ml", tags=["Advanced AI/ML Architecture"]
)
api_router.include_router(sources.router, prefix="/sources", tags=["Data sources"])
