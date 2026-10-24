"use client";

import React, { useMemo, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Bar,
  ComposedChart,
} from "recharts";
import { HourlyForecastItem } from "../../types";
import { formatTemperature, TemperatureUnit } from "../../lib/units";
import { Clock, Droplets, CloudRain } from "lucide-react";

interface HourlyScrubberProps {
  items: HourlyForecastItem[];
  temperatureUnit: TemperatureUnit;
  is24Hour: boolean;
}

export function HourlyScrubber({
  items,
  temperatureUnit,
  is24Hour,
}: HourlyScrubberProps) {
  const [horizonHours, setHorizonHours] = useState<24 | 48 | 72>(24);

  const displayItems = useMemo(() => {
    return (items || []).slice(0, horizonHours);
  }, [items, horizonHours]);

  const chartData = useMemo(() => {
    return displayItems.map((item) => {
      const date = new Date(item.time);
      const hourStr = date.toLocaleTimeString([], {
        hour: "numeric",
        hour12: !is24Hour,
      });
      const tempVal =
        item.temperature_2m !== null && item.temperature_2m !== undefined
          ? temperatureUnit === "F"
            ? Math.round((item.temperature_2m * 9) / 5 + 32)
            : Math.round(item.temperature_2m)
          : null;

      return {
        rawTime: item.time,
        label: hourStr,
        temp: tempVal,
        rainProb: item.precipitation_probability ?? 0,
        rainMm: item.precipitation ?? 0,
        wind: item.wind_speed_10m ?? 0,
      };
    });
  }, [displayItems, temperatureUnit, is24Hour]);

  if (!items || items.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-border-subtle p-6 text-center text-ink-muted">
        No hourly forecast records available for this horizon.
      </div>
    );
  }

  return (
    <div className="w-full bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col gap-5">
      {/* Header with horizon toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand-sky" />
          <h3 className="text-base font-bold text-ink-primary">
            Hourly Forecast Trajectory
          </h3>
          <span className="text-xs text-ink-secondary">
            (Up to {horizonHours} Hours)
          </span>
        </div>

        {/* Horizon selector chips */}
        <div className="flex items-center gap-1.5 self-start sm:self-auto bg-canvas-subtle p-1 rounded-lg border border-border-subtle text-xs">
          {([24, 48, 72] as const).map((h) => (
            <button
              key={h}
              onClick={() => setHorizonHours(h)}
              className={`px-2.5 py-1 rounded font-medium transition-all ${
                horizonHours === h
                  ? "bg-white text-brand-sky shadow-sm font-semibold"
                  : "text-ink-secondary hover:text-ink-primary"
              }`}
            >
              Next {h}h
            </button>
          ))}
        </div>
      </div>

      {/* Interactive Chart */}
      <div className="w-full h-56 pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -25, bottom: 0 }}
          >
            <defs>
              <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0284C7" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#0284C7" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="label"
              stroke="#94A3B8"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              interval={Math.ceil(chartData.length / 8)}
            />
            <YAxis
              stroke="#94A3B8"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              domain={["auto", "auto"]}
              unit={`°`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-white/95 backdrop-blur-md p-3 rounded-xl border border-border-strong shadow-lg text-xs flex flex-col gap-1.5">
                      <span className="font-semibold text-ink-primary">
                        {data.label} ({new Date(data.rawTime).toLocaleDateString("en-IN", { month: "short", day: "numeric" })})
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-brand-sky font-bold text-sm tabular-nums">
                          {data.temp !== null ? `${data.temp}°${temperatureUnit}` : "—"}
                        </span>
                        <span className="text-ink-muted">Temperature</span>
                      </div>
                      <div className="flex items-center gap-2 text-ink-secondary">
                        <Droplets className="w-3.5 h-3.5 text-blue-500" />
                        <span>Precip. Probability: <strong>{data.rainProb}%</strong></span>
                      </div>
                      {data.rainMm > 0 && (
                        <div className="flex items-center gap-2 text-ink-secondary">
                          <CloudRain className="w-3.5 h-3.5 text-blue-600" />
                          <span>Precip. Volume: <strong>{data.rainMm} mm</strong></span>
                        </div>
                      )}
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="temp"
              stroke="#0284C7"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#tempGradient)"
              name="Temperature"
            />
            <Bar
              dataKey="rainProb"
              fill="#93C5FD"
              opacity={0.4}
              yAxisId={0}
              radius={[4, 4, 0, 0]}
              barSize={6}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Horizontal Scroller for Individual Hour Nodes */}
      <div className="flex items-center gap-2.5 overflow-x-auto custom-scrollbar pb-2 pt-1">
        {displayItems.map((item, idx) => {
          const d = new Date(item.time);
          const timeLabel = d.toLocaleTimeString([], {
            hour: "numeric",
            hour12: !is24Hour,
          });
          const rain = item.precipitation_probability ?? 0;
          return (
            <div
              key={idx}
              className="flex flex-col items-center justify-between p-3 min-w-[76px] bg-canvas-subtle/70 rounded-xl border border-border-subtle text-center shrink-0 hover:bg-slate-50 transition-colors"
            >
              <span className="text-[11px] font-medium text-ink-secondary">
                {timeLabel}
              </span>
              <span className="text-base font-bold text-ink-primary my-1 tabular-nums">
                {formatTemperature(item.temperature_2m, temperatureUnit)}
              </span>
              <div className="flex items-center gap-1 text-[10px] text-blue-600 font-medium">
                <Droplets className="w-2.5 h-2.5" />
                <span>{rain}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
