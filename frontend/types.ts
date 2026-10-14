/**
 * Tamil Nadu Climate & Forecast Intelligence Platform
 * TypeScript Type Definitions for REST APIs and Dashboard State
 */

export interface DistrictMeta {
  id: string;
  name: string;
  tamil_name?: string;
  lat: number;
  lon: number;
  elevation_m: number;
  is_coastal: boolean;
  is_hill: boolean;
  region: string;
  normal_annual_rainfall_mm: number;
  nem_normal_mm: number;
  swm_normal_mm: number;
  primary_crops?: string[];
  critical_reservoirs?: string[];
  agriculture_impact?: string;
}

export interface TodaySummary {
  temp_max: number;
  temp_min: number;
  expected_rain_mm: number;
  rain_probability: number;
  sunrise: string;
  sunset: string;
}

export interface CurrentWeatherResponse {
  location_id: string;
  location_name: string;
  tamil_name?: string;
  region: string;
  district_id: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  timestamp: string;
  temperature_2m: number;
  apparent_temperature: number;
  relative_humidity_2m: number;
  precipitation_mm: number;
  wind_speed_10m: number;
  wind_direction_10m: number;
  wind_gusts_10m: number;
  pressure_msl: number;
  cloud_cover: number;
  weather_code: number;
  uv_index: number;
  status: "Clear" | "Cloudy" | "Rainy" | "Storm Risk" | "Hot";
  status_description: string;
  is_stale: boolean;
  data_freshness_minutes: number;
  fetched_at: string;
  quality_flag: string;
  is_cached: boolean;
  today_summary: TodaySummary;
}

export interface HourlyForecastItem {
  time: string;
  hour_label: string;
  temperature: number;
  apparent_temperature: number;
  rain_mm: number;
  precipitation_probability_pct: number;
  humidity: number;
  wind_speed: number;
  dew_point: number;
  condition: string;
  icon: string;
  is_day: boolean;
  is_heavy_rain: boolean;
  is_high_temp: boolean;
}

export interface HourlyForecastResponse {
  district: string;
  hours_count: number;
  forecast_horizon: string;
  hourly: HourlyForecastItem[];
}

export interface DailyForecastItem {
  date: string;
  day_number: number;
  temp_max: number;
  temp_min: number;
  precipitation_sum_mm: number;
  rain_probability: number;
  precipitation_hours: number;
  wind_speed_max: number;
  wind_direction_dominant: number;
  weather_code: number;
  has_warning: boolean;
  warnings: string[];
  temp_change_from_prev: number;
  rain_change_from_prev: number;
  thermal_range: number;
}

export interface DailyForecastResponse {
  district: string;
  days_count: number;
  provider_horizon: string;
  daily: DailyForecastItem[];
}

export interface ComparedDistrictItem {
  district_id: string;
  name: string;
  tamil_name?: string;
  region?: string;
  elevation_m?: number;
  temperature_2m: number;
  apparent_temperature: number;
  relative_humidity_2m: number;
  precipitation_mm: number;
  wind_speed_10m: number;
  pressure_msl: number;
  cloud_cover: number;
  normal_annual_rainfall_mm?: number;
  is_coastal?: boolean;
  is_hill?: boolean;
  error?: string;
}

export interface DistrictComparisonResponse {
  count: number;
  districts: ComparedDistrictItem[];
  rankings: {
    hottest_district: string | null;
    wettest_district: string | null;
    windiest_district: string | null;
  };
}

export interface MapDistrictItem {
  name: string;
  tamil_name: string;
  lat: number;
  lon: number;
  elevation_m: number;
  is_coastal: boolean;
  value: number;
  unit: string;
}

export interface MapWeatherResponse {
  variable: "temperature" | "rainfall" | "humidity" | "wind";
  unit: string;
  timestamp_utc: string;
  geojson_url: string;
  min_value: number;
  max_value: number;
  districts_data: Record<string, MapDistrictItem>;
}
