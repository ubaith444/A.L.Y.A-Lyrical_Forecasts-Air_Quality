"use client";

import React from "react";
import {
  Wind,
  Activity,
  AlertCircle,
  Clock,
  Sparkles,
  CheckCircle2,
  TrendingDown,
  TrendingUp,
  ShieldCheck,
} from "lucide-react";
import { AirQualityResponse } from "../../types/aqi";

interface AQICompanionProps {
  data: AirQualityResponse | null;
  isLoading?: boolean;
}

export function AQICompanion({ data, isLoading }: AQICompanionProps) {
  const aqi = data?.aqi?.indian_aqi ?? data?.aqi?.value;
  const category =
    data?.aqi?.cpcb_details?.category ||
    data?.health_guidance?.category ||
    "Satisfactory";
  const prominent = data?.aqi?.cpcb_details?.dominant_pollutant || "PM2.5";
  const pm25 = data?.pollutants?.pm2_5?.value;
  const pm10 = data?.pollutants?.pm10?.value;

  // Status badge styling
  const getBadge = () => {
    switch (category.toLowerCase()) {
      case "good":
        return {
          bg: "bg-emerald-50 text-emerald-800 border-emerald-200",
          dot: "bg-emerald-500",
          exerciseTip: "Ideal air quality for vigorous outdoor runs and exercise throughout the day.",
        };
      case "satisfactory":
        return {
          bg: "bg-teal-50 text-teal-800 border-teal-200",
          dot: "bg-teal-500",
          exerciseTip: "Good for outdoor activity. Early morning or post-sunset offers the cleanest breeze.",
        };
      case "moderate":
        return {
          bg: "bg-amber-50 text-amber-800 border-amber-200",
          dot: "bg-amber-500",
          exerciseTip: "Sensitive individuals should schedule workouts before 08:00 AM before traffic accumulates.",
        };
      case "poor":
      case "very poor":
      case "severe":
        return {
          bg: "bg-rose-50 text-rose-800 border-rose-200",
          dot: "bg-rose-500",
          exerciseTip: "Consider indoor cardio today. Outdoor exercise not advised during peak traffic hours.",
        };
      default:
        return {
          bg: "bg-slate-50 text-slate-700 border-slate-200",
          dot: "bg-slate-400",
          exerciseTip: "Observing particulate concentrations across the local air monitoring grid.",
        };
    }
  };

  const badge = getBadge();
  const isDataAvailable = aqi !== undefined && aqi !== null;

  return (
    <div className="w-full bg-white rounded-3xl border border-border-subtle p-5 sm:p-6 shadow-sm flex flex-col justify-between gap-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-xl bg-teal-50 flex items-center justify-center text-brand-deepTeal">
            <Wind className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
              Air Quality Companion
            </h3>
            <span className="text-[10px] text-ink-muted">Indian NAQI Standard (CPCB)</span>
          </div>
        </div>

        {/* Clear indication if data is unavailable or outdated */}
        {isDataAvailable ? (
          <div className={`px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center gap-1.5 ${badge.bg}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`}></span>
            <span>{category}</span>
          </div>
        ) : (
          <div className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
            <AlertCircle className="w-3 h-3 text-amber-600" />
            <span>Station Offline</span>
          </div>
        )}
      </div>

      {/* Main AQI Score & PM2.5 / PM10 */}
      <div className="flex items-baseline justify-between">
        <div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-ink-primary font-mono tabular-nums">
              {isDataAvailable ? aqi : "—"}
            </span>
            <span className="text-xs text-ink-muted font-medium">AQI Index</span>
          </div>
          <div className="text-[11px] text-ink-secondary mt-0.5">
            Prominent Pollutant: <strong className="text-ink-primary">{prominent}</strong>
          </div>
        </div>

        {/* PM2.5 & PM10 Compact Badges */}
        <div className="flex items-center gap-2">
          <div className="px-2.5 py-1 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
            <div className="text-[9px] uppercase font-bold text-ink-muted">PM2.5</div>
            <div className="text-xs font-bold text-ink-primary font-mono">
              {pm25 !== null && pm25 !== undefined ? `${Math.round(pm25)} µg/m³` : "—"}
            </div>
          </div>

          <div className="px-2.5 py-1 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
            <div className="text-[9px] uppercase font-bold text-ink-muted">PM10</div>
            <div className="text-xs font-bold text-ink-primary font-mono">
              {pm10 !== null && pm10 !== undefined ? `${Math.round(pm10)} µg/m³` : "—"}
            </div>
          </div>
        </div>
      </div>

      {/* Contextual Exercise Advice */}
      <div className="p-3 rounded-2xl bg-brand-aquaLight/50 border border-brand-aqua/30 flex items-start gap-2.5">
        <Activity className="w-4 h-4 text-brand-deepTeal shrink-0 mt-0.5" />
        <div className="text-xs text-ink-primary leading-relaxed">
          <strong className="text-brand-deepTeal">Outdoor Activity Guidance: </strong>
          <span>{badge.exerciseTip}</span>
        </div>
      </div>

      {/* Hourly Air Quality Trend & Source Note */}
      <div className="pt-1 border-t border-border-subtle/80 flex items-center justify-between text-[11px] text-ink-muted">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3 h-3 text-brand-sky" />
          <span>Next 6 Hours: Stable dispersion</span>
        </div>
        <span className="font-mono text-ink-secondary">CAMS European Ensemble Grid</span>
      </div>
    </div>
  );
}
export default AQICompanion;
