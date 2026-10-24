from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    app_name: str = "Alya Weather API"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"
    open_meteo_air_quality_url: str = "https://air-quality-api.open-meteo.com/v1"
    request_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    provider_retries: int = Field(default=2, ge=0, le=5)
    cache_ttl_seconds: int = Field(default=300, ge=0, le=3600)
    data_dir: Path = BACKEND_DIR / "data"
    database_path: Path = BACKEND_DIR / "data" / "alya.db"
    max_historical_days: int = Field(default=3660, ge=1, le=3660)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            return [
                origin.strip()
                for origin in value.strip("[]").replace('"', "").split(",")
                if origin.strip()
            ]
        return value

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            return value.strip().casefold() in {
                "1",
                "true",
                "yes",
                "on",
                "debug",
                "development",
            }
        return value

    @model_validator(mode="after")
    def restrict_production_cors(self):
        if self.app_env.casefold() == "production" and "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS cannot contain '*' in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
