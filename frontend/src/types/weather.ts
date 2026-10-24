export interface LocationData {
  id: string | null;
  name: string | null;
  state: string | null;
  type: string;
  latitude: float;
  longitude: float;
  timezone: string;
  representation?: string | null;
}

export type float = number;

export interface ProvenanceData {
  source: string;
  retrieved_at: string;
  forecast_issue_time: string | null;
  cache: {
    hit: boolean;
    age_seconds: number;
  };
  freshness: string;
}

export interface CurrentConditions {
  time: string | null;
  values: {
    temperature_2m?: number | null;
    apparent_temperature?: number | null;
    relative_humidity_2m?: number | null;
    precipitation?: number | null;
    weather_code?: number | null;
    cloud_cover?: number | null;
    pressure_msl?: number | null;
    wind_speed_10m?: number | null;
    wind_direction_10m?: number | null;
    uv_index?: number | null;
    [key: string]: number | string | null | undefined;
  };
  units: Record<string, string>;
}

export interface HourlyForecastItem {
  time: string;
  temperature_2m?: number | null;
  apparent_temperature?: number | null;
  relative_humidity_2m?: number | null;
  precipitation_probability?: number | null;
  precipitation?: number | null;
  wind_speed_10m?: number | null;
  wind_direction_10m?: number | null;
  pressure_msl?: number | null;
  cloud_cover?: number | null;
  visibility?: number | null;
  uv_index?: number | null;
  [key: string]: any;
}

export interface DailyForecastItem {
  time: string;
  weather_code?: number | null;
  temperature_2m_max?: number | null;
  temperature_2m_min?: number | null;
  apparent_temperature_max?: number | null;
  apparent_temperature_min?: number | null;
  sunrise?: string | null;
  sunset?: string | null;
  precipitation_sum?: number | null;
  precipitation_probability_max?: number | null;
  wind_speed_10m_max?: number | null;
  wind_direction_10m_dominant?: number | null;
  uv_index_max?: number | null;
  [key: string]: any;
}

export interface WeatherBundleResponse {
  location: LocationData;
  current: CurrentConditions;
  hourly: {
    items: HourlyForecastItem[];
    units: Record<string, string>;
  };
  daily: {
    items: DailyForecastItem[];
    units: Record<string, string>;
  };
  provenance: ProvenanceData;
}

export interface CurrentWeatherResponse {
  location: LocationData;
  current: CurrentConditions;
  provenance: ProvenanceData;
}

export interface HourlyWeatherResponse {
  location: LocationData;
  hourly: {
    items: HourlyForecastItem[];
    units: Record<string, string>;
  };
  provenance: ProvenanceData;
}

export interface DailyWeatherResponse {
  location: LocationData;
  daily: {
    items: DailyForecastItem[];
    units: Record<string, string>;
  };
  provenance: ProvenanceData;
}
