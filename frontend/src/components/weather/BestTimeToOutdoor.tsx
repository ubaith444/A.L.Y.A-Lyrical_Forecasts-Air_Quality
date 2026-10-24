"use client";

import React from "react";
import {
  Compass,
  Footprints,
  Sun,
  Sunset,
  Sunrise,
  Car,
  Umbrella,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
} from "lucide-react";
import { DailyForecastItem, HourlyForecastItem } from "../../types/weather";
import { AirQualityResponse } from "../../types/aqi";
import { computeBestTimeToGo } from "../../lib/intelligence";

interface BestTimeToOutdoorProps {
  hourlyItems: HourlyForecastItem[];
  dailyItems: DailyForecastItem[];
  aqiData?: AirQualityResponse | null;
}

export function BestTimeToOutdoor({
  hourlyItems,
  dailyItems,
  aqiData,
}: BestTimeToOutdoorProps) {
  const decisions = computeBestTimeToGo(hourlyItems, dailyItems, aqiData);

  return (
    <div className="w-full bg-white rounded-3xl border border-border-subtle p-5 sm:p-6 shadow-sm flex flex-col justify-between gap-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-xl bg-amber-50 flex items-center justify-center text-amber-700">
            <Footprints className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
              The Best Time to Go
            </h3>
            <span className="text-[10px] text-ink-muted">Actionable Decision Windows</span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] text-brand-deepTeal font-medium bg-brand-aquaLight px-2.5 py-0.5 rounded-full border border-brand-aqua/30">
          <Sparkles className="w-3 h-3" />
          <span>Activity Planner</span>
        </div>
      </div>

      {/* Grid of Decision Blocks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {/* Card 1: Outdoor Exercise Window */}
        <div className="p-3.5 rounded-2xl bg-canvas-subtle border border-border-subtle flex flex-col justify-between gap-2 transition-all hover:border-brand-sky/40">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-ink-muted flex items-center gap-1">
              <Footprints className="w-3 h-3 text-brand-sky" />
              Exercise & Jogging Window
            </span>
            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800">
              {decisions.exerciseWindow.rating}
            </span>
          </div>

          <div>
            <div className="text-base font-bold text-ink-primary font-mono">
              {decisions.exerciseWindow.bestTime}
            </div>
            <p className="text-xs text-ink-secondary mt-1 leading-snug">
              {decisions.exerciseWindow.summary}
            </p>
          </div>

          <div className="text-[10px] text-ink-muted flex items-center gap-1">
            <span>Air: {decisions.exerciseWindow.aqiCategory}</span>
            <span>•</span>
            <span>Temp: {decisions.exerciseWindow.temp}°C</span>
          </div>
        </div>

        {/* Card 2: Commute & Transit Window */}
        <div className="p-3.5 rounded-2xl bg-canvas-subtle border border-border-subtle flex flex-col justify-between gap-2 transition-all hover:border-brand-sky/40">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-ink-muted flex items-center gap-1">
              <Car className="w-3 h-3 text-brand-deepTeal" />
              Commute & Travel Window
            </span>
            {decisions.commuteWindow.eveningRainRisk ? (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-100 text-amber-800 flex items-center gap-1">
                <Umbrella className="w-2.5 h-2.5" />
                Rain Risk
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800">
                Clear Transit
              </span>
            )}
          </div>

          <div>
            <div className="text-sm font-bold text-ink-primary">
              {decisions.commuteWindow.eveningRainRisk
                ? "Pack Umbrella for Evening"
                : "Smooth All-Day Transit"}
            </div>
            <p className="text-xs text-ink-secondary mt-1 leading-snug">
              {decisions.commuteWindow.recommendation}
            </p>
          </div>

          <div className="text-[10px] text-ink-muted">
            {decisions.commuteWindow.peakRainTime
              ? `Evening rain peak: around ${decisions.commuteWindow.peakRainTime}`
              : "Zero traffic rain delay predicted"}
          </div>
        </div>
      </div>

      {/* Astronomy Footer: Sunrise & Sunset */}
      <div className="pt-2 border-t border-border-subtle/80 flex items-center justify-between text-xs text-ink-secondary">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <Sunrise className="w-3.5 h-3.5 text-amber-500" />
            <span>Rise: <strong className="text-ink-primary font-mono">{decisions.sunTimes.sunrise}</strong></span>
          </div>
          <div className="flex items-center gap-1.5">
            <Sunset className="w-3.5 h-3.5 text-orange-500" />
            <span>Set: <strong className="text-ink-primary font-mono">{decisions.sunTimes.sunset}</strong></span>
          </div>
        </div>

        <span className="text-[11px] text-ink-muted">{decisions.sunTimes.daylightDuration}</span>
      </div>
    </div>
  );
}
export default BestTimeToOutdoor;
