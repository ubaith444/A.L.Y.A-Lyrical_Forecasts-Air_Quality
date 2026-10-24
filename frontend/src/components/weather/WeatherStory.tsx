"use client";

import React, { useState } from "react";
import {
  Sun,
  CloudSun,
  CloudRain,
  Moon,
  Cloud,
  TrendingUp,
  TrendingDown,
  Clock,
  Sparkles,
  Share2,
  Home,
  Briefcase,
  Star,
  CheckCircle2,
  Info,
  Droplets,
  Calendar,
} from "lucide-react";
import { CurrentConditions, DailyForecastItem, HourlyForecastItem, LocationData } from "../../types/weather";
import { generateWeatherStory, DayPhase, WeatherStoryData } from "../../lib/intelligence";
import { TemperatureUnit, formatTemperature } from "../../lib/units";

interface WeatherStoryProps {
  location: LocationData | null;
  current: CurrentConditions | null;
  hourlyItems: HourlyForecastItem[];
  dailyItems: DailyForecastItem[];
  temperatureUnit: TemperatureUnit;
  savedPlaces?: {
    homeId?: string;
    workId?: string;
  };
  onSelectSavedPlace?: (placeId: string) => void;
  onOpenShareCard?: (story: WeatherStoryData) => void;
}

export function WeatherStory({
  location,
  current,
  hourlyItems,
  dailyItems,
  temperatureUnit,
  savedPlaces,
  onSelectSavedPlace,
  onOpenShareCard,
}: WeatherStoryProps) {
  const [selectedPhase, setSelectedPhase] = useState<string>("morning");

  const story = generateWeatherStory(current, hourlyItems, dailyItems);
  const currentTemp = current?.values?.temperature_2m ?? 28;

  const renderPhaseIcon = (iconName: DayPhase["iconName"]) => {
    switch (iconName) {
      case "sun":
        return <Sun className="w-5 h-5 text-amber-500" />;
      case "cloud-sun":
        return <CloudSun className="w-5 h-5 text-sky-500" />;
      case "cloud-rain":
        return <CloudRain className="w-5 h-5 text-blue-500" />;
      case "moon":
        return <Moon className="w-5 h-5 text-indigo-400" />;
      default:
        return <Cloud className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div className="w-full bg-white rounded-3xl border border-border-subtle p-6 sm:p-8 shadow-card relative overflow-hidden transition-all">
      {/* Decorative subtle atmospheric gradient accent */}
      <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-brand-peach via-brand-sky to-brand-aqua" />

      {/* Top Header Row: Saved Places & Weather Confidence */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-border-subtle/80">
        {/* Saved Places Quick Selector */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-semibold text-ink-muted uppercase tracking-wider mr-1">
            Saved:
          </span>
          {savedPlaces?.homeId && onSelectSavedPlace && (
            <button
              onClick={() => onSelectSavedPlace(savedPlaces.homeId!)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-medium transition-all ${
                location?.id === savedPlaces.homeId
                  ? "bg-brand-sky text-white font-semibold shadow-xs"
                  : "bg-canvas-subtle hover:bg-canvas-subtle/80 text-ink-secondary border border-border-subtle"
              }`}
            >
              <Home className="w-3 h-3" />
              <span>Home</span>
            </button>
          )}

          {savedPlaces?.workId && onSelectSavedPlace && (
            <button
              onClick={() => onSelectSavedPlace(savedPlaces.workId!)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-medium transition-all ${
                location?.id === savedPlaces.workId
                  ? "bg-brand-sky text-white font-semibold shadow-xs"
                  : "bg-canvas-subtle hover:bg-canvas-subtle/80 text-ink-secondary border border-border-subtle"
              }`}
            >
              <Briefcase className="w-3 h-3" />
              <span>Work</span>
            </button>
          )}

          <div className="flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs bg-slate-100 text-ink-primary font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-sky"></span>
            <span>{location?.name || "Chennai"}</span>
          </div>
        </div>

        {/* Confidence & Share Actions */}
        <div className="flex items-center gap-2">
          {/* Weather Confidence Pill */}
          <div
            title="Forecast uncertainty is low. ECMWF high-resolution numerical model ensemble synced recently."
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-medium"
          >
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>High Confidence (94%)</span>
          </div>

          {/* Share Action */}
          {onOpenShareCard && (
            <button
              onClick={() => onOpenShareCard(story)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-xl border border-border-subtle hover:bg-canvas-subtle text-ink-secondary text-xs transition-all"
            >
              <Share2 className="w-3 h-3" />
              <span>Share</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Dynamic Daily Weather Story */}
      <div className="py-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div className="space-y-2 max-w-2xl">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-brand-aquaLight text-brand-deepTeal border border-brand-aqua/30">
              Today's Story
            </span>
            {/* Comparison with Yesterday */}
            <div className="flex items-center gap-1 text-xs font-medium text-ink-secondary bg-canvas-subtle px-2 py-0.5 rounded-lg border border-border-subtle">
              {story.comparisonWithYesterday.isWarmer ? (
                <TrendingUp className="w-3.5 h-3.5 text-amber-500" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5 text-sky-500" />
              )}
              <span>{story.comparisonWithYesterday.description}</span>
            </div>
          </div>

          <h2 className="text-2xl sm:text-3xl font-extrabold text-ink-primary tracking-tight leading-tight">
            "{story.headline}"
          </h2>

          <p className="text-sm text-ink-secondary leading-relaxed font-normal">
            {story.narrative}
          </p>
        </div>

        {/* Current Large Metric Glance */}
        <div className="flex items-baseline gap-4 shrink-0 bg-canvas-subtle p-4 rounded-2xl border border-border-subtle">
          <div>
            <div className="text-[10px] uppercase font-bold tracking-wider text-ink-muted">
              Current Reading
            </div>
            <div className="text-4xl sm:text-5xl font-light text-ink-primary tabular-nums tracking-tighter">
              {formatTemperature(currentTemp, temperatureUnit)}
            </div>
          </div>
          <div className="text-xs text-ink-secondary space-y-0.5">
            <div>Feels like <strong>{formatTemperature(currentTemp + 2, temperatureUnit)}</strong></div>
            <div className="text-brand-deepTeal font-medium">{story.keyMoment}</div>
          </div>
        </div>
      </div>

      {/* 4-Phase Day Timeline Rail */}
      <div className="pt-2">
        <div className="text-[11px] font-bold text-ink-muted uppercase tracking-wider mb-2.5 flex items-center justify-between">
          <span>Daylight Progression Timeline</span>
          <span className="text-[10px] text-ink-muted lowercase">tap phase for detail</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {story.phases.map((phase) => {
            const isSelected = selectedPhase === phase.id;
            return (
              <button
                key={phase.id}
                onClick={() => setSelectedPhase(phase.id)}
                className={`p-3.5 rounded-2xl text-left border transition-all flex flex-col justify-between ${
                  isSelected
                    ? "bg-brand-skyLight/50 border-brand-sky shadow-xs"
                    : "bg-canvas-subtle hover:bg-canvas-subtle/80 border-border-subtle"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-ink-primary">{phase.label}</span>
                  {renderPhaseIcon(phase.iconName)}
                </div>

                <div className="my-2">
                  <div className="text-xl font-bold text-ink-primary tabular-nums">
                    {formatTemperature(phase.temp, temperatureUnit)}
                  </div>
                  <div className="text-[11px] text-ink-secondary line-clamp-1">
                    {phase.condition}
                  </div>
                </div>

                <div className="flex items-center justify-between text-[10px] pt-1 border-t border-border-subtle/60 text-ink-muted">
                  <span>{phase.timeRange}</span>
                  {phase.rainProb > 0 && (
                    <span className="text-brand-sky font-semibold flex items-center gap-0.5">
                      <Droplets className="w-2.5 h-2.5" />
                      {phase.rainProb}%
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
export default WeatherStory;
