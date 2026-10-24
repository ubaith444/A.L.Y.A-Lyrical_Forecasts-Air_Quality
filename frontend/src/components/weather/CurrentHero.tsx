"use client";

import React from "react";
import {
  Cloud,
  Droplets,
  Wind as WindIcon,
  Sun,
  Eye,
  Compass,
  Gauge,
  Clock,
  Sparkles,
} from "lucide-react";
import { CurrentConditions, LocationData, ProvenanceData } from "../../types";
import {
  formatDateLocal,
  formatTemperature,
  formatTimeLocal,
  formatWindSpeed,
  TemperatureUnit,
  WindSpeedUnit,
  windDegreeToDirection,
} from "../../lib/units";
import { generateLyricalSynopsis, getWeatherConditionLabel } from "../../lib/lyrical";

interface CurrentHeroProps {
  location: LocationData | null;
  current: CurrentConditions | null;
  provenance: ProvenanceData | null;
  temperatureUnit: TemperatureUnit;
  windSpeedUnit: WindSpeedUnit;
  is24Hour: boolean;
}

export function CurrentHero({
  location,
  current,
  provenance,
  temperatureUnit,
  windSpeedUnit,
  is24Hour,
}: CurrentHeroProps) {
  if (!current || !location) {
    return (
      <div className="w-full bg-white rounded-2xl border border-border-subtle p-8 animate-pulse flex flex-col gap-4">
        <div className="h-6 w-48 bg-slate-100 rounded" />
        <div className="h-20 w-36 bg-slate-100 rounded" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 bg-slate-100 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const values = current.values || {};
  const temp = values.temperature_2m;
  const apparentTemp = values.apparent_temperature;
  const humidity = values.relative_humidity_2m;
  const windSpeed = values.wind_speed_10m;
  const windDirection = values.wind_direction_10m;
  const pressure = values.pressure_msl;
  const cloudCover = values.cloud_cover;
  const uvIndex = values.uv_index;
  const weatherCode = values.weather_code as number | undefined;

  const lyricalText = generateLyricalSynopsis({
    temperature: temp,
    weatherCode,
    cloudCover,
    precipitation: values.precipitation as number | undefined,
    windSpeed,
  });

  const conditionLabel = getWeatherConditionLabel(weatherCode);

  return (
    <div className="w-full bg-gradient-to-br from-white via-white to-canvas-subtle rounded-2xl border border-border-subtle p-6 sm:p-8 shadow-card relative overflow-hidden transition-all">
      {/* Subtle atmospheric accent bar aligned with A.L.Y.A visual identity */}
      <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-brand-aqua via-brand-sky to-brand-peach" />

      {/* Top row: Location & Indian Local Time */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-6 border-b border-border-subtle/70">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-ink-primary tracking-tight">
              {location.name || "Unknown Station"}
            </h2>
            <span className="text-xs uppercase font-medium tracking-wide px-2 py-0.5 rounded-full bg-brand-skyLight text-brand-sky">
              {location.state || "India"}
            </span>
            {location.type === "district" && (
              <span className="text-[11px] font-normal text-ink-muted bg-slate-100 px-2 py-0.5 rounded">
                District Center
              </span>
            )}
          </div>
          <p className="text-xs text-ink-secondary mt-1">
            {formatDateLocal(current.time)} • Local Time {formatTimeLocal(current.time, is24Hour)} IST
          </p>
        </div>

        {/* Freshness & Attribution */}
        {provenance && (
          <div className="flex items-center gap-2 text-[11px] text-ink-muted sm:text-right">
            <Clock className="w-3.5 h-3.5 text-brand-sky" />
            <span>
              {provenance.cache?.hit
                ? `Cached ${Math.round(provenance.cache.age_seconds)}s ago`
                : "Live Provider Ingestion"}
            </span>
          </div>
        )}
      </div>

      {/* Middle row: Hero Temperature & Lyrical Synopsis */}
      <div className="py-6 sm:py-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex items-baseline gap-4">
            <span className="text-6xl sm:text-7xl lg:text-8xl font-light text-ink-primary tabular-nums tracking-tighter">
              {formatTemperature(temp, temperatureUnit)}
            </span>
            <div className="flex flex-col gap-1">
              <span className="text-base sm:text-lg font-semibold text-ink-primary">
                {conditionLabel}
              </span>
              {apparentTemp !== null && apparentTemp !== undefined && (
                <span className="text-xs text-ink-secondary">
                  Feels like {formatTemperature(apparentTemp, temperatureUnit)}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Lyrical synopsis badge */}
        <div className="max-w-md bg-brand-aquaLight/40 backdrop-blur-sm border border-brand-aqua/30 rounded-xl p-4 flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-brand-deepTeal shrink-0 mt-0.5" />
          <div>
            <span className="text-[10px] font-semibold tracking-wider uppercase text-brand-deepTeal block">
              Atmospheric Synopsis
            </span>
            <p className="text-sm font-medium text-ink-primary italic mt-0.5 leading-relaxed">
              "{lyricalText}"
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Glanceable Essential Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-4 border-t border-border-subtle/70">
        {/* Humidity */}
        <div className="bg-white/80 rounded-xl p-3 border border-border-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-ink-secondary text-xs">
            <span>Humidity</span>
            <Droplets className="w-4 h-4 text-sky-500" />
          </div>
          <span className="text-lg font-semibold text-ink-primary mt-2 tabular-nums">
            {humidity !== null && humidity !== undefined ? `${Math.round(humidity)}%` : "—"}
          </span>
          <span className="text-[10px] text-ink-muted">Relative humidity</span>
        </div>

        {/* Wind */}
        <div className="bg-white/80 rounded-xl p-3 border border-border-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-ink-secondary text-xs">
            <span>Wind</span>
            <WindIcon className="w-4 h-4 text-teal-500" />
          </div>
          <span className="text-lg font-semibold text-ink-primary mt-2 tabular-nums">
            {formatWindSpeed(windSpeed, windSpeedUnit)}
          </span>
          <span className="text-[10px] text-ink-muted flex items-center gap-1">
            <Compass className="w-3 h-3 text-brand-sky inline" />
            {windDegreeToDirection(windDirection)} ({windDirection ?? "—"}°)
          </span>
        </div>

        {/* Cloud Cover */}
        <div className="bg-white/80 rounded-xl p-3 border border-border-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-ink-secondary text-xs">
            <span>Cloud Cover</span>
            <Cloud className="w-4 h-4 text-slate-400" />
          </div>
          <span className="text-lg font-semibold text-ink-primary mt-2 tabular-nums">
            {cloudCover !== null && cloudCover !== undefined ? `${Math.round(cloudCover)}%` : "—"}
          </span>
          <span className="text-[10px] text-ink-muted">Sky coverage</span>
        </div>

        {/* UV Index */}
        <div className="bg-white/80 rounded-xl p-3 border border-border-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-ink-secondary text-xs">
            <span>UV Index</span>
            <Sun className="w-4 h-4 text-amber-500" />
          </div>
          <span className="text-lg font-semibold text-ink-primary mt-2 tabular-nums">
            {uvIndex !== null && uvIndex !== undefined ? Math.round(uvIndex) : "—"}
          </span>
          <span className="text-[10px] text-ink-muted">
            {uvIndex && uvIndex > 7
              ? "Very High"
              : uvIndex && uvIndex > 5
              ? "Moderate"
              : "Low"}
          </span>
        </div>

        {/* Atmospheric Pressure */}
        <div className="bg-white/80 rounded-xl p-3 border border-border-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-ink-secondary text-xs">
            <span>Pressure</span>
            <Gauge className="w-4 h-4 text-indigo-400" />
          </div>
          <span className="text-lg font-semibold text-ink-primary mt-2 tabular-nums">
            {pressure !== null && pressure !== undefined ? `${Math.round(pressure)} hPa` : "—"}
          </span>
          <span className="text-[10px] text-ink-muted">Mean sea level</span>
        </div>

        {/* Precipitation */}
        <div className="bg-white/80 rounded-xl p-3 border border-border-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-ink-secondary text-xs">
            <span>Precipitation</span>
            <Droplets className="w-4 h-4 text-blue-500" />
          </div>
          <span className="text-lg font-semibold text-ink-primary mt-2 tabular-nums">
            {values.precipitation !== null && values.precipitation !== undefined
              ? `${values.precipitation} mm`
              : "0 mm"}
          </span>
          <span className="text-[10px] text-ink-muted">Past hour volume</span>
        </div>
      </div>
    </div>
  );
}
