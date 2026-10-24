from datetime import date
from typing import Any

from pydantic import BaseModel, Field, model_validator


class HistoricalIngestionRequest(BaseModel):
    location_id: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class EvaluationRequest(BaseModel):
    dataset_id: str = Field(min_length=1, max_length=100)
    target_variable: str = Field(
        default="temperature_2m_mean",
        pattern="^(temperature_2m_mean|precipitation_sum|relative_humidity_2m_mean)$",
    )


class Pagination(BaseModel):
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)
    total: int = Field(ge=0)


class LocationResponse(BaseModel):
    id: str | None
    name: str | None
    state: str | None
    type: str
    latitude: float
    longitude: float
    timezone: str
    representation: str | None = None


class LocationsResponse(BaseModel):
    items: list[LocationResponse]
    pagination: Pagination
    catalogue_coverage: str


class ProvenanceResponse(BaseModel):
    source: str
    retrieved_at: str
    forecast_issue_time: str | None
    cache: dict[str, Any]
    freshness: str


class ConditionsResponse(BaseModel):
    time: str | None
    values: dict[str, float | int | None]
    units: dict[str, str]


class ForecastSeriesResponse(BaseModel):
    items: list[dict[str, Any]]
    units: dict[str, str]


class WeatherResponse(BaseModel):
    location: LocationResponse
    current: ConditionsResponse
    hourly: ForecastSeriesResponse
    daily: ForecastSeriesResponse
    provenance: ProvenanceResponse


class CurrentWeatherResponse(BaseModel):
    location: LocationResponse
    current: ConditionsResponse
    provenance: ProvenanceResponse


class HourlyWeatherResponse(BaseModel):
    location: LocationResponse
    hourly: ForecastSeriesResponse
    provenance: ProvenanceResponse


class DailyWeatherResponse(BaseModel):
    location: LocationResponse
    daily: ForecastSeriesResponse
    provenance: ProvenanceResponse


class AirQualityResponse(BaseModel):
    location: LocationResponse
    timestamp: str | None
    aqi: dict[str, Any]
    pollutants: dict[str, dict[str, Any]]
    health_guidance: dict[str, str]
    data_quality: dict[str, str]
    provenance: ProvenanceResponse


class PaginatedResponse(BaseModel):
    items: list[dict[str, Any]]
    pagination: Pagination
