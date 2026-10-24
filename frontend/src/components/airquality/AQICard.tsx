"use client";

import React from "react";
import { Wind, ShieldAlert, AlertCircle, Info, Activity, CheckCircle2 } from "lucide-react";
import { AirQualityResponse } from "../../types";
import { getCPCBConfig, getUSEPAConfig } from "../../lib/aqi-utils";

interface AQICardProps {
  data: AirQualityResponse | null;
}

export function AQICard({ data }: AQICardProps) {
  if (!data) {
    return (
      <div className="w-full bg-white rounded-2xl border border-border-subtle p-6 animate-pulse flex flex-col gap-4">
        <div className="h-6 w-36 bg-slate-100 rounded" />
        <div className="h-24 w-full bg-slate-100 rounded-xl" />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-20 bg-slate-100 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  const aqi = data.aqi;
  const cpcbDetails = aqi.cpcb_details;
  const indianAqiVal = aqi.indian_aqi;
  const cpcbConfig = getCPCBConfig(indianAqiVal);

  const usAqiVal = aqi.value;
  const usConfig = getUSEPAConfig(usAqiVal);

  const pollutants = data.pollutants || {};

  return (
    <div className="w-full bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <Wind className="w-5 h-5 text-brand-sky" />
          <div>
            <h3 className="text-base font-bold text-ink-primary">
              Air Quality Intelligence
            </h3>
            <p className="text-xs text-ink-secondary">
              National Ambient Air Quality Monitoring & Multi-Standard Comparison
            </p>
          </div>
        </div>

        <span className="text-[11px] font-medium text-ink-muted bg-canvas-subtle px-2.5 py-1 rounded-md border border-border-subtle self-start sm:self-auto">
          {data.data_quality?.status || "Provider Modelled"}
        </span>
      </div>

      {/* Hero AQI Card: Indian CPCB NAQI Focus */}
      <div
        className={`p-5 rounded-2xl border ${cpcbConfig.borderClass} ${cpcbConfig.bgClass} flex flex-col md:flex-row items-start md:items-center justify-between gap-6 transition-all`}
      >
        <div className="flex items-center gap-5">
          {/* Numeric Badge */}
          <div
            className="w-20 h-20 rounded-2xl flex flex-col items-center justify-center text-white font-bold shadow-md shrink-0"
            style={{ backgroundColor: cpcbConfig.badgeHex }}
          >
            <span className="text-2xl font-black tabular-nums">
              {indianAqiVal !== null && indianAqiVal !== undefined ? indianAqiVal : "—"}
            </span>
            <span className="text-[10px] tracking-wider uppercase opacity-90">
              NAQI
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span
                className={`text-lg font-bold ${cpcbConfig.textClass}`}
              >
                {cpcbConfig.category}
              </span>
              <span className="text-[11px] font-medium bg-white/80 text-ink-secondary px-2 py-0.5 rounded border border-border-subtle">
                Official CPCB NAQI
              </span>
            </div>

            {/* Dominant Pollutant */}
            {cpcbDetails?.dominant_pollutant && (
              <p className="text-xs text-ink-secondary mt-0.5">
                Responsible Pollutant:{" "}
                <strong className="text-ink-primary uppercase">
                  {cpcbDetails.dominant_pollutant.replace("_", ".")}
                </strong>
              </p>
            )}

            {/* Health Guidance */}
            <p className="text-xs text-ink-primary mt-2 font-medium max-w-lg leading-relaxed">
              {data.health_guidance?.message || cpcbConfig.guidanceText}
            </p>
          </div>
        </div>

        {/* Global Standards Comparison Pillar */}
        <div className="bg-white/90 backdrop-blur-sm p-3.5 rounded-xl border border-border-subtle/80 flex flex-col gap-2 shrink-0 w-full md:w-56 text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-ink-muted">
            Global Scales Reference
          </span>
          <div className="flex items-center justify-between">
            <span className="text-ink-secondary">US EPA AQI:</span>
            <span className={`font-bold tabular-nums ${usConfig.colorClass}`}>
              {usAqiVal !== null ? `${usAqiVal} (${usConfig.category})` : "—"}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-ink-secondary">European EAQI:</span>
            <span className="font-bold tabular-nums text-ink-primary">
              {aqi.european_aqi !== null && aqi.european_aqi !== undefined
                ? aqi.european_aqi
                : "—"}
            </span>
          </div>
        </div>
      </div>

      {/* Disclaimers & Calculation Criteria Note */}
      <div className="bg-canvas-subtle p-3 rounded-xl border border-border-subtle flex items-start gap-2.5 text-xs text-ink-secondary">
        <Info className="w-4 h-4 text-brand-sky shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Standards Disclaimer:</strong> {aqi.standards_disclaimer}{" "}
          {aqi.indian_aqi_status}
        </p>
      </div>

      {/* Individual Pollutants Breakdown Grid */}
      <div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-ink-muted mb-3">
          Pollutant Concentrations & Sub-Indices
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { key: "pm2_5", label: "PM2.5", sub: "Fine Particulate (24h)" },
            { key: "pm10", label: "PM10", sub: "Coarse Particulate (24h)" },
            { key: "nitrogen_dioxide", label: "NO₂", sub: "Nitrogen Dioxide (24h)" },
            { key: "sulphur_dioxide", label: "SO₂", sub: "Sulphur Dioxide (24h)" },
            { key: "carbon_monoxide", label: "CO", sub: "Carbon Monoxide (8h)" },
            { key: "ozone", label: "O₃", sub: "Surface Ozone (8h)" },
          ].map((pol) => {
            const detail = pollutants[pol.key];
            const isAvail = detail?.status === "available" && detail?.value !== null && detail?.value !== undefined;
            const subIndex = cpcbDetails?.sub_indices?.[pol.key];

            return (
              <div
                key={pol.key}
                className="bg-canvas-subtle/70 rounded-xl p-3 border border-border-subtle flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-ink-primary">
                      {pol.label}
                    </span>
                    {subIndex !== undefined && (
                      <span className="text-[10px] font-semibold text-brand-sky bg-brand-skyLight px-1.5 py-0.2 rounded">
                        Sub: {Math.round(subIndex)}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-ink-muted block mt-0.5 truncate">
                    {pol.sub}
                  </span>
                </div>

                <div className="mt-3">
                  <span className="text-base font-bold text-ink-primary tabular-nums block">
                    {isAvail ? detail.value : "—"}
                  </span>
                  <span className="text-[10px] text-ink-muted">
                    {isAvail ? detail.unit || "μg/m³" : "Unavailable"}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
