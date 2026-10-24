"use client";

import React, { useState, useEffect } from "react";
import {
  Flame,
  CloudRain,
  TrendingUp,
  BarChart3,
  Calendar,
  AlertTriangle,
  Info,
  Layers,
} from "lucide-react";
import {
  HeatPatternsResponse,
  HistoricalDataset,
  HistoricalSummaryResponse,
  MonsoonResponse,
} from "../../types";
import {
  createHistoricalIngestion,
  fetchHeatPatterns,
  fetchHistoricalDatasets,
  fetchHistoricalSummary,
  fetchMonsoonAnalysis,
} from "../../lib/api";
import { TemperatureUnit } from "../../lib/units";

interface ClimateDashboardProps {
  locationId: string | null;
  temperatureUnit: TemperatureUnit;
}

export function ClimateDashboard({
  locationId,
  temperatureUnit,
}: ClimateDashboardProps) {
  const [datasets, setDatasets] = useState<HistoricalDataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);

  const [heatPatterns, setHeatPatterns] = useState<HeatPatternsResponse | null>(null);
  const [monsoon, setMonsoon] = useState<MonsoonResponse | null>(null);
  const [summary, setSummary] = useState<HistoricalSummaryResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [ingestStatus, setIngestStatus] = useState<string | null>(null);

  // Load available historical datasets
  const loadData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // First try station-specific datasets
      const res = await fetchHistoricalDatasets(locationId || undefined);
      let items = res.items || [];

      // If no datasets exist specifically for this station, fallback to all available datasets
      if (items.length === 0) {
        const allRes = await fetchHistoricalDatasets();
        if (allRes.items && allRes.items.length > 0) {
          items = allRes.items;
        }
      }

      setDatasets(items);
      if (items.length > 0) {
        setSelectedDatasetId((prev) => (prev && items.some((i) => i.id === prev) ? prev : items[0].id));
      } else {
        setSelectedDatasetId(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load historical datasets");
    } finally {
      setLoading(false);
    }
  }, [locationId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle on-demand ingestion
  const handleTriggerIngestion = async () => {
    const loc = locationId || "chennai";
    try {
      setIsIngesting(true);
      setIngestStatus("Queuing ERA5 reanalysis ingestion for " + loc + " (2023)...");
      await createHistoricalIngestion({
        locationId: loc,
        startDate: "2023-01-01",
        endDate: "2023-12-31",
      });
      setIngestStatus("Ingestion job completed! Refreshing dataset archive...");
      setTimeout(() => {
        loadData();
        setIsIngesting(false);
        setIngestStatus(null);
      }, 3000);
    } catch (err: any) {
      setIngestStatus("Ingestion error: " + (err.message || "Request failed"));
      setIsIngesting(false);
    }
  };

  // Load analytics when selectedDatasetId changes
  useEffect(() => {
    if (!selectedDatasetId) return;
    let active = true;

    async function loadAnalytics() {
      try {
        const [heatRes, monsoonRes, summaryRes] = await Promise.allSettled([
          fetchHeatPatterns({ datasetId: selectedDatasetId!, thresholdCelsius: 40.0 }),
          fetchMonsoonAnalysis({ datasetId: selectedDatasetId!, startMonth: 6, endMonth: 9 }),
          fetchHistoricalSummary({ datasetId: selectedDatasetId!, variable: "temperature_2m_mean", period: "monthly" }),
        ]);

        if (!active) return;
        if (heatRes.status === "fulfilled") setHeatPatterns(heatRes.value);
        if (monsoonRes.status === "fulfilled") setMonsoon(monsoonRes.value);
        if (summaryRes.status === "fulfilled") setSummary(summaryRes.value);
      } catch (err: any) {
        console.error("Error loading climate analytics:", err);
      }
    }

    loadAnalytics();
    return () => {
      active = false;
    };
  }, [selectedDatasetId]);

  return (
    <div className="w-full flex flex-col gap-6">
      {/* Overview Header & Dataset Selector */}
      <div className="bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-sky" />
            <h3 className="text-base font-bold text-ink-primary">
              Climate Intelligence & Extreme Pattern Analysis
            </h3>
          </div>
          <p className="text-xs text-ink-secondary mt-1">
            Grounded in ECMWF ERA5 Atmospheric Reanalysis Archives
          </p>
        </div>

        {/* Dataset dropdown and Ingestion Trigger */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {datasets.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-ink-secondary font-medium">Dataset:</span>
              <select
                value={selectedDatasetId || ""}
                onChange={(e) => setSelectedDatasetId(e.target.value)}
                className="bg-canvas-subtle border border-border-subtle rounded-lg px-3 py-1.5 font-medium text-ink-primary outline-none focus:border-brand-aqua"
              >
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.location_id.toUpperCase()} ({d.start_date.substring(0, 4)} — {d.row_count} records)
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={handleTriggerIngestion}
            disabled={isIngesting}
            className="px-3 py-1.5 rounded-lg bg-brand-aquaLight hover:bg-brand-aqua/20 border border-brand-aqua/40 text-brand-deepTeal font-bold transition-all disabled:opacity-50"
          >
            {isIngesting ? "Ingesting ERA5 Reanalysis..." : `+ Ingest 1-Yr ERA5 Data for ${locationId || "Current Station"}`}
          </button>
        </div>
      </div>

      {/* Quick Station Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 text-xs bg-canvas-subtle/60 p-3 rounded-xl border border-border-subtle">
        <span className="text-ink-muted text-[11px] font-semibold">Available Regional Archives:</span>
        {["chennai", "coimbatore", "district-nilgiris", "new-delhi"].map((loc) => {
          const hasDs = datasets.some((d) => d.location_id === loc);
          const isCurrent = datasets.find((d) => d.id === selectedDatasetId)?.location_id === loc;
          return (
            <button
              key={loc}
              onClick={() => {
                const targetDs = datasets.find((d) => d.location_id === loc);
                if (targetDs) setSelectedDatasetId(targetDs.id);
              }}
              disabled={!hasDs}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                isCurrent
                  ? "bg-brand-deepTeal text-white shadow-sm ring-2 ring-brand-aqua/40"
                  : hasDs
                  ? "bg-white border border-border-subtle hover:border-brand-aqua text-ink-primary shadow-xs"
                  : "bg-slate-50 text-ink-muted opacity-50 cursor-not-allowed"
              }`}
            >
              {loc === "district-nilgiris" ? "Nilgiris (Ooty)" : loc.replace(/-/g, " ").toUpperCase()}
              {hasDs ? " • 365d" : " (Not yet ingested)"}
            </button>
          );
        })}
      </div>

      {ingestStatus && (
        <div className="p-3 bg-brand-aquaLight/60 border border-brand-aqua/40 rounded-xl text-xs text-brand-deepTeal font-medium">
          {ingestStatus}
        </div>
      )}

      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-64 bg-white rounded-2xl border border-border-subtle p-6 animate-pulse" />
          <div className="h-64 bg-white rounded-2xl border border-border-subtle p-6 animate-pulse" />
        </div>
      )}

      {!loading && datasets.length === 0 && (
        <div className="bg-white rounded-2xl border border-border-subtle p-8 text-center flex flex-col items-center gap-4">
          <Layers className="w-10 h-10 text-brand-aqua" />
          <div>
            <h4 className="text-sm font-bold text-ink-primary">
              No Stored Historical Datasets for Current Station
            </h4>
            <p className="text-xs text-ink-secondary max-w-md leading-relaxed mt-1">
              Historical ECMWF ERA5 reanalysis datasets can be ingested on demand with 1 click:
            </p>
          </div>
          <button
            onClick={handleTriggerIngestion}
            disabled={isIngesting}
            className="px-4 py-2 rounded-xl bg-brand-deepTeal text-white text-xs font-bold transition-all hover:bg-[#084846] shadow-sm disabled:opacity-50"
          >
            {isIngesting ? "Ingesting ERA5 Reanalysis..." : "Ingest 1-Year ERA5 Dataset Now"}
          </button>
        </div>
      )}

      {/* Heat Patterns & Monsoon Analytics Cards */}
      {heatPatterns && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Heat Patterns Card */}
          <div className="bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col justify-between gap-5">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
                <div className="flex items-center gap-2">
                  <Flame className="w-4 h-4 text-orange-500" />
                  <h4 className="text-sm font-bold text-ink-primary">
                    Heat Pattern & Heatwave Analytics
                  </h4>
                </div>
                <span className="text-[11px] font-semibold text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full border border-orange-200">
                  Threshold: ≥{heatPatterns.threshold_celsius}°C
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                <div className="bg-canvas-subtle p-3 rounded-xl border border-border-subtle text-center">
                  <span className="text-[11px] text-ink-muted block">Days ≥35°C</span>
                  <span className="text-xl font-bold text-ink-primary tabular-nums mt-1 block">
                    {heatPatterns.days_above_35c}
                  </span>
                </div>
                <div className="bg-orange-50/60 p-3 rounded-xl border border-orange-100 text-center">
                  <span className="text-[11px] text-orange-700 block">Days ≥40°C</span>
                  <span className="text-xl font-bold text-orange-700 tabular-nums mt-1 block">
                    {heatPatterns.days_above_40c}
                  </span>
                </div>
                <div className="bg-red-50/60 p-3 rounded-xl border border-red-100 text-center">
                  <span className="text-[11px] text-red-700 block">Days ≥45°C</span>
                  <span className="text-xl font-bold text-red-700 tabular-nums mt-1 block">
                    {heatPatterns.days_above_45c}
                  </span>
                </div>
                <div className="bg-canvas-subtle p-3 rounded-xl border border-border-subtle text-center">
                  <span className="text-[11px] text-ink-muted block">Max Streak</span>
                  <span className="text-xl font-bold text-ink-primary tabular-nums mt-1 block">
                    {heatPatterns.max_consecutive_hot_days} days
                  </span>
                </div>
              </div>

              {/* Peak Temperature Recorded */}
              <div className="mt-4 p-3 rounded-xl bg-canvas-subtle border border-border-subtle flex items-center justify-between text-xs">
                <div>
                  <span className="text-ink-muted block">Peak Max Temperature</span>
                  <span className="font-bold text-ink-primary text-sm tabular-nums">
                    {heatPatterns.peak_temperature.temperature}°C
                  </span>
                </div>
                <span className="text-ink-secondary text-[11px]">
                  Recorded on: <strong>{heatPatterns.peak_temperature.date}</strong>
                </span>
              </div>

              {/* Summer Season Breakdown */}
              <div className="mt-3 p-3 rounded-xl bg-canvas-subtle border border-border-subtle text-xs flex flex-col gap-1">
                <span className="font-semibold text-ink-primary">
                  {heatPatterns.summer_season_summary.months}
                </span>
                <div className="flex items-center justify-between text-ink-secondary">
                  <span>Summer Average Max Temp:</span>
                  <span className="font-bold text-ink-primary tabular-nums">
                    {heatPatterns.summer_season_summary.mean_temperature ?? "—"}°C
                  </span>
                </div>
                <div className="flex items-center justify-between text-ink-secondary">
                  <span>Summer Hot Days (≥40°C):</span>
                  <span className="font-bold text-orange-600 tabular-nums">
                    {heatPatterns.summer_season_summary.hot_days_count}
                  </span>
                </div>
              </div>
            </div>

            <p className="text-[11px] text-ink-muted italic border-t border-border-subtle/70 pt-2">
              *{heatPatterns.source_note}
            </p>
          </div>

          {/* Monsoon Analysis Card */}
          {monsoon && (
            <div className="bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col justify-between gap-5">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
                  <div className="flex items-center gap-2">
                    <CloudRain className="w-4 h-4 text-blue-500" />
                    <h4 className="text-sm font-bold text-ink-primary">
                      Monsoon Season Precipitation
                    </h4>
                  </div>
                  <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                    Months: June–Sept
                  </span>
                </div>

                <div className="p-6 bg-gradient-to-br from-blue-50/60 to-white rounded-xl border border-blue-100 flex flex-col items-center justify-center my-4 text-center">
                  <span className="text-xs uppercase font-semibold text-blue-600 tracking-wider">
                    Total Monsoon Rainfall
                  </span>
                  <span className="text-4xl font-extrabold text-blue-900 tabular-nums my-2">
                    {monsoon.rainfall_total !== null ? `${monsoon.rainfall_total} mm` : "—"}
                  </span>
                  <span className="text-xs text-ink-secondary">
                    Monitored over {monsoon.days_with_data} valid days in season
                  </span>
                </div>

                <div className="p-3 bg-canvas-subtle rounded-xl border border-border-subtle text-xs text-ink-secondary">
                  <p>
                    <strong>Methodology:</strong> {monsoon.note} Calculated directly from daily reanalysis accumulation sums without synthetic imputation.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-ink-muted border-t border-border-subtle/70 pt-2">
                <Info className="w-3.5 h-3.5 text-brand-sky shrink-0" />
                <span>ERA5 reanalysis product; does not replace IMD rain gauge observations.</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
