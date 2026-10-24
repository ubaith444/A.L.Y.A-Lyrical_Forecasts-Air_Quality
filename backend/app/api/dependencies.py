from functools import lru_cache

from app.core.config import BACKEND_DIR, get_settings
from app.core.database import Database
from app.services.cache import ResponseCache
from app.services.locations import LocationService
from app.services.providers import OpenMeteoClient


@lru_cache
def get_database() -> Database:
    return Database(get_settings().database_path)


@lru_cache
def get_location_service() -> LocationService:
    return LocationService(BACKEND_DIR / "app" / "data" / "india_locations.json")


@lru_cache
def get_provider() -> OpenMeteoClient:
    settings = get_settings()
    return OpenMeteoClient(
        settings.open_meteo_base_url,
        settings.open_meteo_air_quality_url,
        settings.request_timeout_seconds,
        settings.provider_retries,
    )


@lru_cache
def get_cache() -> ResponseCache:
    settings = get_settings()
    return ResponseCache(get_database(), settings.cache_ttl_seconds)
