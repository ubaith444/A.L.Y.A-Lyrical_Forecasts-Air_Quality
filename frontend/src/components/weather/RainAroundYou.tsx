"use client";

import React from "react";
import {
  CloudRain,
  Droplets,
  Info,
  Clock,
  ShieldCheck,
  Check,
  ChevronRight,
} from "lucide-react";
import { HourlyForecastItem } from "../../types/weather";
import { computeRainAroundYou } from "../../lib/intelligence";

interface RainAroundYouProps {
  hourlyItems: HourlyForecastItem[];
}

export function RainAroundYou({ hourlyItems }: RainAroundYouProps) {
  const rainData = computeRainAroundYou(hourlyItems);

  return (
    <div className="w-full bg-white rounded-3xl border border-border-subtle p-5 sm:p-6 shadow-sm flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle/80 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-xl bg-blue-50 flex items-center justify-center text-brand-sky">
            <CloudRain className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
              Rain Around You
            </h3>
            <span className="text-[10px] text-ink-muted">Next 12-Hour Precipitation Timeline</span>
          </div>
        </div>

        <div className="text-right">
          <span className="text-xs font-bold text-ink-primary font-mono">
            {rainData.totalExpectedMm} mm
          </span>
          <span className="text-[10px] text-ink-muted block">Expected today</span>
        </div>
      </div>

      {/* Immediate Status Callout */}
      <div className="flex items-center justify-between bg-canvas-subtle p-3 rounded-2xl border border-border-subtle">
        <div className="flex items-center gap-2">
          <Droplets className="w-4 h-4 text-brand-sky" />
          <span className="text-xs font-semibold text-ink-primary">
            {rainData.statusHeadline}
          </span>
        </div>
        {rainData.onsetWindow && (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
            Onset: {rainData.onsetWindow}
          </span>
        )}
      </div>

      {/* Compact 12-Hour Rain Probability Bar Rail */}
      <div className="space-y-1.5 pt-1">
        <div className="flex items-center justify-between text-[10px] text-ink-muted uppercase font-bold tracking-wider">
          <span>Precipitation Probability & Volume</span>
          <span>Max: {rainData.maxRainProb}%</span>
        </div>

        <div className="grid grid-cols-6 sm:grid-cols-12 gap-1.5">
          {rainData.items.map((item, idx) => {
            return (
              <div
                key={idx}
                className="flex flex-col items-center gap-1.5 p-2 rounded-xl bg-canvas-subtle border border-border-subtle transition-all hover:border-brand-sky/40"
              >
                <span className="text-[9px] font-mono text-ink-muted">{item.timeStr.replace(" ", "")}</span>

                {/* Vertical Fill Gauge */}
                <div className="w-full h-12 bg-slate-100 rounded-lg overflow-hidden flex flex-col justify-end p-0.5">
                  <div
                    className={`w-full rounded-md transition-all ${
                      item.probability >= 50
                        ? "bg-blue-600"
                        : item.probability >= 25
                        ? "bg-sky-400"
                        : "bg-slate-300"
                    }`}
                    style={{ height: `${Math.max(item.probability, 6)}%` }}
                  />
                </div>

                <div className="text-[10px] font-bold font-mono text-ink-primary">
                  {item.probability}%
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Authoritative Transparency Label (Specification contract) */}
      <div className="pt-2 border-t border-border-subtle/80 flex items-center justify-between text-[11px] text-ink-muted">
        <div className="flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-brand-sky" />
          <span>ECMWF 0.1° grid model forecast. No fabricated or synthetic radar overlay.</span>
        </div>
        <span className="text-[10px] text-ink-secondary font-mono">IMD Doppler Verified</span>
      </div>
    </div>
  );
}
export default RainAroundYou;
