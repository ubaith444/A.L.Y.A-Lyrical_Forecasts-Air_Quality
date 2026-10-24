"use client";

import React, { useMemo } from "react";
import { Calendar, Sunrise, Sunset, Droplets, Sun } from "lucide-react";
import { DailyForecastItem } from "../../types";
import { formatTemperature, TemperatureUnit } from "../../lib/units";
import { getWeatherConditionLabel } from "../../lib/lyrical";

interface DailyForecastProps {
  items: DailyForecastItem[];
  temperatureUnit: TemperatureUnit;
}

export function DailyForecast({ items, temperatureUnit }: DailyForecastProps) {
  // Find global min and max across all 14 days to scale the horizontal range bars proportionally
  const { globalMin, globalMax } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;
    (items || []).forEach((item) => {
      if (item.temperature_2m_min !== null && item.temperature_2m_min !== undefined) {
        min = Math.min(min, item.temperature_2m_min);
      }
      if (item.temperature_2m_max !== null && item.temperature_2m_max !== undefined) {
        max = Math.max(max, item.temperature_2m_max);
      }
    });
    if (min === Infinity) min = 15;
    if (max === -Infinity) max = 35;
    return { globalMin: min, globalMax: max };
  }, [items]);

  if (!items || items.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-border-subtle p-6 text-center text-ink-muted">
        No daily forecast records available.
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-brand-sky" />
          <h3 className="text-base font-bold text-ink-primary">
            14-Day Extended Outlook
          </h3>
        </div>
        <span className="text-xs text-ink-secondary">
          {items.length} Days Available
        </span>
      </div>

      {/* Days List */}
      <div className="flex flex-col divide-y divide-border-subtle/70">
        {items.map((item, index) => {
          const date = new Date(item.time);
          const dayName =
            index === 0
              ? "Today"
              : index === 1
              ? "Tomorrow"
              : date.toLocaleDateString("en-IN", { weekday: "short" });
          const dateStr = date.toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
          });

          const minTemp = item.temperature_2m_min ?? 0;
          const maxTemp = item.temperature_2m_max ?? 0;
          const rangeSpan = Math.max(1, globalMax - globalMin);
          const leftPercent = Math.max(
            0,
            Math.min(100, ((minTemp - globalMin) / rangeSpan) * 100)
          );
          const widthPercent = Math.max(
            5,
            Math.min(100 - leftPercent, ((maxTemp - minTemp) / rangeSpan) * 100)
          );

          const rainSum = item.precipitation_sum ?? 0;
          const condition = getWeatherConditionLabel(item.weather_code);

          return (
            <div
              key={index}
              className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-ink-secondary hover:bg-slate-50/70 px-2 rounded-xl transition-colors"
            >
              {/* Day title & date */}
              <div className="flex items-center gap-3 w-36 shrink-0">
                <span className="font-semibold text-ink-primary text-sm w-16">
                  {dayName}
                </span>
                <span className="text-ink-muted text-[11px]">{dateStr}</span>
              </div>

              {/* Condition & Rain */}
              <div className="flex items-center gap-3 w-40 shrink-0">
                <span className="text-xs text-ink-primary font-medium truncate">
                  {condition}
                </span>
                {rainSum > 0 && (
                  <span className="flex items-center gap-1 text-[11px] text-blue-600 font-semibold shrink-0">
                    <Droplets className="w-3 h-3" />
                    {rainSum.toFixed(1)}mm
                  </span>
                )}
              </div>

              {/* Horizontal Visual Range Slider */}
              <div className="flex items-center gap-3 flex-1 min-w-[180px]">
                <span className="text-ink-secondary font-medium w-9 text-right tabular-nums">
                  {formatTemperature(item.temperature_2m_min, temperatureUnit)}
                </span>

                {/* Range Bar container */}
                <div className="relative flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="absolute top-0 bottom-0 rounded-full bg-gradient-to-r from-sky-400 to-amber-500"
                    style={{
                      left: `${leftPercent}%`,
                      width: `${widthPercent}%`,
                    }}
                  />
                </div>

                <span className="text-ink-primary font-bold w-9 tabular-nums">
                  {formatTemperature(item.temperature_2m_max, temperatureUnit)}
                </span>
              </div>

              {/* UV Max badge */}
              {item.uv_index_max !== null && item.uv_index_max !== undefined && (
                <div className="hidden lg:flex items-center gap-1 text-[11px] text-amber-600 w-16 justify-end">
                  <Sun className="w-3 h-3" />
                  <span>UV {Math.round(item.uv_index_max)}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
