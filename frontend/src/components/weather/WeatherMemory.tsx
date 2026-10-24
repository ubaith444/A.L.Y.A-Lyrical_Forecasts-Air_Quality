"use client";

import React, { useState } from "react";
import {
  History,
  TrendingUp,
  TrendingDown,
  CloudRain,
  Flame,
  Snowflake,
  Compass,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Info,
} from "lucide-react";
import { CurrentConditions, DailyForecastItem, LocationData } from "../../types/weather";
import { computeWeatherMemory } from "../../lib/intelligence";

interface WeatherMemoryProps {
  location: LocationData | null;
  current: CurrentConditions | null;
  dailyItems: DailyForecastItem[];
}

export function WeatherMemory({
  location,
  current,
  dailyItems,
}: WeatherMemoryProps) {
  const [showVerificationDetail, setShowVerificationDetail] = useState(false);
  const memory = computeWeatherMemory(current, dailyItems);

  return (
    <div className="w-full bg-white rounded-3xl border border-border-subtle p-5 sm:p-6 shadow-sm flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-xl bg-purple-50 flex items-center justify-center text-purple-700">
            <History className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
              Weather Memory & Seasonal Context
            </h3>
            <span className="text-[10px] text-ink-muted">Historical Comparative Intelligence</span>
          </div>
        </div>

        <span className="text-[11px] font-mono text-ink-muted">Past 7 Days & Baseline</span>
      </div>

      {/* 3 Metric Comparison Blocks */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Metric 1: Warmer or Cooler than Yesterday */}
        <div className="p-3.5 rounded-2xl bg-canvas-subtle border border-border-subtle flex flex-col justify-between gap-1.5">
          <span className="text-[10px] uppercase font-bold text-ink-muted">Yesterday Comparison</span>
          <div className="flex items-center gap-1.5 text-sm font-bold text-ink-primary">
            {memory.tempComparison.deltaC >= 0 ? (
              <TrendingUp className="w-4 h-4 text-amber-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-sky-500" />
            )}
            <span>{memory.tempComparison.text}</span>
          </div>
          <span className="text-[10px] text-ink-secondary">Relative to same hour yesterday</span>
        </div>

        {/* Metric 2: Weekly Rainfall this week vs last week */}
        <div className="p-3.5 rounded-2xl bg-canvas-subtle border border-border-subtle flex flex-col justify-between gap-1.5">
          <span className="text-[10px] uppercase font-bold text-ink-muted">Weekly Cumulative Rain</span>
          <div className="flex items-baseline justify-between">
            <span className="text-sm font-bold text-ink-primary font-mono">
              {memory.weeklyRainfall.thisWeekMm} mm
            </span>
            <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
              +{memory.weeklyRainfall.trendPct}% vs last wk
            </span>
          </div>
          <span className="text-[10px] text-ink-secondary">Last week recorded: {memory.weeklyRainfall.lastWeekMm} mm</span>
        </div>

        {/* Metric 3: Recent Temperature Extremes */}
        <div className="p-3.5 rounded-2xl bg-canvas-subtle border border-border-subtle flex flex-col justify-between gap-1.5">
          <span className="text-[10px] uppercase font-bold text-ink-muted">Recent Extremes (7d)</span>
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1 font-medium text-amber-700">
              <Flame className="w-3.5 h-3.5 text-amber-500" />
              <span>{memory.recentExtremes.warmestDay.day}: {memory.recentExtremes.warmestDay.tempC}°C</span>
            </div>
            <div className="flex items-center gap-1 font-medium text-sky-700">
              <Snowflake className="w-3.5 h-3.5 text-sky-500" />
              <span>{memory.recentExtremes.coolestNight.day}: {memory.recentExtremes.coolestNight.tempC}°C</span>
            </div>
          </div>
          <span className="text-[10px] text-ink-secondary">Recorded weekly high & nocturnal low</span>
        </div>
      </div>

      {/* Monsoon Watch Section */}
      <div className="p-3.5 rounded-2xl bg-brand-aquaLight/40 border border-brand-aqua/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-brand-deepTeal text-white">
              Monsoon Watch
            </span>
            <span className="text-xs font-bold text-ink-primary">{memory.monsoonWatch.phase}</span>
          </div>
          <p className="text-xs text-ink-secondary leading-snug">
            {memory.monsoonWatch.description}
          </p>
        </div>

        <div className="shrink-0 text-left sm:text-right">
          <span className="text-xs font-bold text-brand-deepTeal">
            {memory.monsoonWatch.status}
          </span>
          <span className="text-[10px] text-ink-muted block font-mono">
            {memory.monsoonWatch.departurePct >= 0 ? "+" : ""}{memory.monsoonWatch.departurePct}% IMD Departure
          </span>
        </div>
      </div>

      {/* Forecast vs Actual Expandable Section */}
      <div className="pt-1">
        <button
          onClick={() => setShowVerificationDetail(!showVerificationDetail)}
          className="flex items-center justify-between w-full text-xs text-ink-secondary hover:text-ink-primary font-medium py-1 transition-all"
        >
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Forecast vs Actual Accuracy: <strong>{memory.forecastVsActual.accuracyPct}% consistency</strong></span>
          </div>
          {showVerificationDetail ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showVerificationDetail && (
          <div className="mt-2.5 p-3 rounded-2xl bg-canvas-subtle border border-border-subtle text-xs text-ink-secondary space-y-1.5 animate-in fade-in duration-200">
            <div className="flex justify-between">
              <span>Mean Absolute Temperature Error:</span>
              <strong className="text-ink-primary font-mono">±{memory.forecastVsActual.meanTempDiffC}°C</strong>
            </div>
            <div className="flex justify-between">
              <span>Ground Verification Source:</span>
              <span className="font-mono text-ink-primary">{memory.forecastVsActual.verifiedStation}</span>
            </div>
            <p className="text-[11px] text-ink-muted pt-1 leading-snug">
              Past 24-hour predictions are routinely backtested against ERA5 reanalysis and physical AWS station observations to prevent model drift.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
export default WeatherMemory;
