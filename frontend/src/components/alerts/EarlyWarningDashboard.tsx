"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  ShieldAlert,
  AlertTriangle,
  Zap,
  CloudRain,
  Wind,
  Waves,
  Mountain,
  CheckCircle2,
  Bell,
  Send,
  RefreshCw,
  Radio,
  Sliders,
  Info,
  MapPin,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Smartphone,
  Mail,
  Flame,
} from "lucide-react";
import { LocationData } from "../../types";
import {
  fetchEarlyWarningAlerts,
  fetchRegionalEarlyWarning,
  simulateAlertDispatch,
  fetchAlertHistory,
} from "../../lib/api";

interface EarlyWarningDashboardProps {
  currentLocation: LocationData | null;
  onSelectLocation?: (locationId: string) => void;
}

export function EarlyWarningDashboard({
  currentLocation,
  onSelectLocation,
}: EarlyWarningDashboardProps) {
  const activeLocId = currentLocation?.id || "chennai";

  // Data states
  const [dossier, setDossier] = useState<any | null>(null);
  const [regionalData, setRegionalData] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Simulation controls
  const [simTemp, setSimTemp] = useState<number>(32.0);
  const [simWindGust, setSimWindGust] = useState<number>(35.0);
  const [simPrecip24h, setSimPrecip24h] = useState<number>(45.0);
  const [simAntecedent72h, setSimAntecedent72h] = useState<number>(60.0);
  const [simTsunamiActive, setSimTsunamiActive] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  // Dispatch Simulator state
  const [dispatchHazard, setDispatchHazard] = useState<string>("heavy_rainfall");
  const [dispatchLevel, setDispatchLevel] = useState<number>(2);
  const [dispatchHeadline, setDispatchHeadline] = useState<string>(
    "Heavy Inundation & Waterlogging Warning across Low-Lying Arteries"
  );
  const [dispatchStatus, setDispatchStatus] = useState<any | null>(null);
  const [dispatchHistory, setDispatchHistory] = useState<any[]>([]);

  // Load alert dossier for active location
  const loadAlerts = async (overrideParams?: any) => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        locationId: activeLocId,
        simTemp: isSimulating ? simTemp : undefined,
        simWindGust: isSimulating ? simWindGust : undefined,
        simPrecip24h: isSimulating ? simPrecip24h : undefined,
        simAntecedent72h: isSimulating ? simAntecedent72h : undefined,
        simTsunamiActive: isSimulating ? simTsunamiActive : undefined,
        ...overrideParams,
      };
      const res = await fetchEarlyWarningAlerts(params);
      setDossier(res);
    } catch (err: any) {
      setError(err.message || "Failed loading early warning alerts");
    } finally {
      setLoading(false);
    }
  };

  // Load statewide overview and dispatch history
  const loadRegionalAndHistory = async () => {
    try {
      const [reg, hist] = await Promise.all([
        fetchRegionalEarlyWarning("Tamil Nadu"),
        fetchAlertHistory(activeLocId),
      ]);
      setRegionalData(reg);
      setDispatchHistory(hist.items || []);
    } catch (err) {
      console.warn("Failed loading regional data or history:", err);
    }
  };

  useEffect(() => {
    loadAlerts();
    loadRegionalAndHistory();
  }, [activeLocId]);

  useEffect(() => {
    if (isSimulating) {
      loadAlerts();
    }
  }, [simTemp, simWindGust, simPrecip24h, simAntecedent72h, simTsunamiActive, isSimulating]);

  // Handle alert dispatch simulation
  const handleDispatch = async () => {
    try {
      const res = await simulateAlertDispatch({
        hazard: dispatchHazard,
        level: dispatchLevel,
        locationId: activeLocId,
        headline: dispatchHeadline,
        instructions: [
          "Seek sturdy indoor shelter.",
          "Avoid driving through waterlogged underpasses.",
          "Follow directives from District Administration and TNSDMA.",
        ],
      });
      setDispatchStatus(res);
      await loadRegionalAndHistory();
    } catch (err: any) {
      setDispatchStatus({ error: err.message || "Dispatch failed" });
    }
  };

  // Tamil Nadu District Showcase Pills
  const tamilNaduFocusDistricts = [
    { id: "chennai", label: "Chennai", badge: "Coastal / Urban Flood" },
    { id: "cuddalore", label: "Cuddalore", badge: "Cyclone / Storm Surge" },
    { id: "nagapattinam", label: "Nagapattinam", badge: "Cauvery Seaboard / Tsunami Zone" },
    { id: "district-nilgiris", label: "Nilgiris (Ooty)", badge: "Western Ghats Landslide" },
    { id: "kodaikanal", label: "Kodaikanal", badge: "Palani Hills Montane Slope" },
    { id: "coimbatore", label: "Coimbatore", badge: "Western Plains / Noyyal Basin" },
    { id: "madurai", label: "Madurai", badge: "Vaigai River Plain" },
    { id: "kanyakumari", label: "Kanyakumari", badge: "Peninsular Oceanic Convergence" },
  ];

  const overallAlert = dossier?.overall_alert;
  const hazards = dossier?.hazards;

  return (
    <div className="flex flex-col gap-6 animate-in fade-in duration-300">
      {/* 1. Header Banner & State Focus */}
      <div className="bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col gap-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center text-red-600 border border-red-200">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-ink-primary">
                  A.L.Y.A Early Warning & Multi-Hazard Disaster Alert System
                </h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                  TAMIL NADU & INDIA
                </span>
              </div>
              <p className="text-xs text-ink-secondary">
                Combines live numerical weather data, official disaster advisories (IMD, INCOIS, TNSDMA), geospatial terrain susceptibility, and calibrated ML early-warning models.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setIsSimulating(!isSimulating);
                if (isSimulating) {
                  // reset to live
                  loadAlerts({
                    simTemp: undefined,
                    simWindGust: undefined,
                    simPrecip24h: undefined,
                    simAntecedent72h: undefined,
                    simTsunamiActive: false,
                  });
                }
              }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                isSimulating
                  ? "bg-amber-500 text-white border-amber-600 shadow-xs"
                  : "bg-slate-50 text-ink-secondary hover:text-ink-primary border-border-subtle"
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>{isSimulating ? "Simulation Active" : "Stress-Test Simulator"}</span>
            </button>

            <button
              onClick={() => loadAlerts()}
              disabled={loading}
              className="p-2 rounded-lg bg-slate-50 text-ink-secondary hover:text-ink-primary border border-border-subtle transition-all"
              title="Refresh Alert Feeds"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Tamil Nadu District Fast-Switcher */}
        <div className="flex flex-col gap-2 pt-1 border-t border-border-subtle">
          <div className="flex items-center justify-between text-xs font-semibold text-ink-secondary">
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-brand-sky" />
              Tamil Nadu Vulnerability Zones Quick Selector:
            </span>
            <span className="text-[11px] text-ink-muted">
              Active: {dossier?.location?.name || activeLocId.toUpperCase()} ({dossier?.location?.state})
            </span>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 custom-scrollbar">
            {tamilNaduFocusDistricts.map((d) => {
              const isSelected = activeLocId === d.id;
              return (
                <button
                  key={d.id}
                  onClick={() => {
                    if (onSelectLocation) {
                      onSelectLocation(d.id);
                    }
                  }}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border shrink-0 flex items-center gap-1.5 ${
                    isSelected
                      ? "bg-brand-deepTeal text-white border-brand-deepTeal shadow-xs"
                      : "bg-slate-50 text-ink-secondary hover:bg-slate-100 hover:text-ink-primary border-border-subtle"
                  }`}
                >
                  <span>{d.label}</span>
                  <span className={`text-[9px] px-1.5 py-0.2 rounded font-normal ${
                    isSelected ? "bg-white/20 text-white" : "bg-white text-ink-muted border border-slate-200"
                  }`}>
                    {d.badge.split("/")[0]}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2. OVERALL ALERT STATUS BANNER */}
      {overallAlert && (
        <div
          className={`p-5 rounded-2xl border shadow-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-all ${
            overallAlert.level === 3
              ? "bg-red-50/90 border-red-300 text-red-950"
              : overallAlert.level === 2
              ? "bg-orange-50/90 border-orange-300 text-orange-950"
              : overallAlert.level === 1
              ? "bg-amber-50/90 border-amber-300 text-amber-950"
              : "bg-emerald-50/90 border-emerald-300 text-emerald-950"
          }`}
        >
          <div className="flex items-start sm:items-center gap-3.5">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 text-white font-black text-sm shadow-sm ${
                overallAlert.level === 3
                  ? "bg-red-600"
                  : overallAlert.level === 2
                  ? "bg-orange-500"
                  : overallAlert.level === 1
                  ? "bg-amber-500"
                  : "bg-emerald-600"
              }`}
            >
              L{overallAlert.level}
            </div>

            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-sm sm:text-base">
                  {overallAlert.level_title}
                </span>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-white/70 border border-black/10">
                  {dossier.location.name.toUpperCase()}
                </span>
                {overallAlert.active_hazards_count > 0 && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-800 border border-red-300">
                    {overallAlert.active_hazards_count} Active Threat{overallAlert.active_hazards_count > 1 ? "s" : ""}
                  </span>
                )}
              </div>
              <p className="text-xs leading-relaxed opacity-90 max-w-2xl">
                {overallAlert.description}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 text-xs font-semibold bg-white/80 px-3 py-2 rounded-xl border border-black/10">
            <Radio className="w-3.5 h-3.5 text-brand-sky animate-pulse" />
            <span>Primary Threat: {overallAlert.primary_threat}</span>
          </div>
        </div>
      )}

      {/* 3. OFFICIAL DISASTER ADVISORY VS AI-PREDICTED RISK SEPARATION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Official Disaster Advisory (IMD / INCOIS / TNSDMA) */}
        <div className="bg-white rounded-2xl border border-sky-200/80 p-5 shadow-card flex flex-col gap-3 relative overflow-hidden">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-sky-700" />
              <h4 className="text-xs font-bold text-sky-950 uppercase tracking-wider">
                Official Government Disaster Advisory (Authoritative Source)
              </h4>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800">
              IMD & TNSDMA
            </span>
          </div>

          <p className="text-xs text-ink-primary font-medium leading-relaxed">
            {dossier?.official_authority_status?.status || "Routine Meteorological Surveillance Active."}
          </p>

          <div className="p-3 bg-sky-50/70 border border-sky-100 rounded-xl text-[11px] text-sky-900 flex flex-col gap-1">
            <div className="flex justify-between">
              <span>Issuing Authority:</span>
              <span className="font-semibold">{dossier?.official_authority_status?.issued_by}</span>
            </div>
            <div className="flex justify-between">
              <span>Bulletin Reference:</span>
              <span className="font-semibold">{dossier?.official_authority_status?.bulletin_number}</span>
            </div>
            <div className="flex justify-between">
              <span>Statutory Mandate:</span>
              <span>Disaster Management Act, 2005</span>
            </div>
          </div>

          <div className="text-[10px] text-ink-muted flex items-center gap-1.5 pt-1">
            <Info className="w-3 h-3 text-sky-600" />
            <span>Official alerts supersede all statistical and machine-learning models.</span>
          </div>
        </div>

        {/* Right: A.L.Y.A AI/ML Multi-Hazard Risk Scoring */}
        <div className="bg-white rounded-2xl border border-emerald-200/80 p-5 shadow-card flex flex-col gap-3 relative overflow-hidden">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-emerald-700" />
              <h4 className="text-xs font-bold text-emerald-950 uppercase tracking-wider">
                A.L.Y.A Calibrated Machine-Learning Risk Engine
              </h4>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
              ML RISK SCORES
            </span>
          </div>

          <p className="text-xs text-ink-primary font-medium leading-relaxed">
            Independent physical instability and geotechnical risk classification calibrated on ERA5-Land reanalysis and IMD precipitation baselines.
          </p>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="p-2.5 rounded-lg bg-slate-50 border border-border-subtle flex flex-col">
              <span className="text-ink-muted text-[10px]">Lightning Risk Score:</span>
              <span className="font-bold text-ink-primary tabular-nums">
                {hazards?.lightning?.risk_score_pct}% ({hazards?.lightning?.severity_label})
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-border-subtle flex flex-col">
              <span className="text-ink-muted text-[10px]">Thunderstorm Score:</span>
              <span className="font-bold text-ink-primary tabular-nums">
                {hazards?.thunderstorm?.risk_score_pct}% ({hazards?.thunderstorm?.severity_label})
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-border-subtle flex flex-col">
              <span className="text-ink-muted text-[10px]">Landslide Terrain Index:</span>
              <span className="font-bold text-ink-primary tabular-nums">
                {hazards?.landslide?.risk_score_pct}% ({hazards?.landslide?.severity_label})
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-50 border border-border-subtle flex flex-col">
              <span className="text-ink-muted text-[10px]">Tsunami Alert Source:</span>
              <span className="font-bold text-purple-700">
                INCOIS Official Only
              </span>
            </div>
          </div>

          <div className="text-[10px] text-ink-muted flex items-center gap-1.5 pt-1">
            <Info className="w-3 h-3 text-emerald-600" />
            <span>AI scores provide localized early detection; never claim unverified disaster certainty.</span>
          </div>
        </div>
      </div>

      {/* 4. THE 5 DISASTER HAZARDS DETAIL CARDS */}
      <div className="flex flex-col gap-4">
        <h4 className="text-sm font-bold text-ink-primary flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-brand-sky" />
          Location-Aware Hazard Dossier for {dossier?.location?.name}
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* HAZARD 1: LIGHTNING ALERT */}
          {hazards?.lightning && (
            <div className="bg-white rounded-2xl border border-border-subtle p-5 shadow-card flex flex-col justify-between gap-4">
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-amber-500" />
                    <span className="font-bold text-xs text-ink-primary">1. Lightning Hazard</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      hazards.lightning.level >= 2
                        ? "bg-red-100 text-red-800 border border-red-300"
                        : hazards.lightning.level === 1
                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                        : "bg-emerald-100 text-emerald-800"
                    }`}
                  >
                    Level {hazards.lightning.level} • {hazards.lightning.severity_label}
                  </span>
                </div>

                <div className="text-xs font-semibold text-ink-primary">
                  {hazards.lightning.status}
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-border-subtle text-[11px] flex flex-col gap-1.5">
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">Convective Instability Score:</span>
                    <span className="font-bold text-ink-primary">{hazards.lightning.risk_score_pct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">Thermal Forcing:</span>
                    <span>{hazards.lightning.convective_indicators?.thermal_forcing}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">Peak Wind Gust:</span>
                    <span>{hazards.lightning.convective_indicators?.wind_gust_kmh} km/h</span>
                  </div>
                </div>

                {/* Safety Instructions */}
                <div className="flex flex-col gap-1 text-[11px]">
                  <span className="font-bold text-amber-900">Outdoor Safety Actions:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-ink-secondary">
                    {hazards.lightning.instructions.map((ins: string, idx: number) => (
                      <li key={idx}>{ins}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="text-[10px] text-ink-muted pt-2 border-t border-border-subtle">
                Source: {hazards.lightning.source} (Confidence: {hazards.lightning.model_confidence * 100}%)
              </div>
            </div>
          )}

          {/* HAZARD 2: THUNDERSTORM & WIND SQUALL */}
          {hazards?.thunderstorm && (
            <div className="bg-white rounded-2xl border border-border-subtle p-5 shadow-card flex flex-col justify-between gap-4">
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
                  <div className="flex items-center gap-2">
                    <Wind className="w-4 h-4 text-sky-600" />
                    <span className="font-bold text-xs text-ink-primary">2. Thunderstorm & Wind Squall</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      hazards.thunderstorm.level >= 2
                        ? "bg-red-100 text-red-800 border border-red-300"
                        : hazards.thunderstorm.level === 1
                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                        : "bg-emerald-100 text-emerald-800"
                    }`}
                  >
                    Level {hazards.thunderstorm.level} • {hazards.thunderstorm.severity_label}
                  </span>
                </div>

                <div className="text-xs font-semibold text-ink-primary">
                  {hazards.thunderstorm.status}
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-border-subtle text-[11px] flex flex-col gap-1.5">
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">Expected Wind Gust:</span>
                    <span className="font-bold text-ink-primary">{hazards.thunderstorm.expected_wind_gust_kmh} km/h</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">Squall Potential:</span>
                    <span>{hazards.thunderstorm.expected_wind_gust_kmh >= 50 ? "High Squall Risk" : "Standard Downdraft"}</span>
                  </div>
                </div>

                {/* Safety Instructions */}
                <div className="flex flex-col gap-1 text-[11px]">
                  <span className="font-bold text-sky-900">Protective Measures:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-ink-secondary">
                    {hazards.thunderstorm.instructions.map((ins: string, idx: number) => (
                      <li key={idx}>{ins}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="text-[10px] text-ink-muted pt-2 border-t border-border-subtle">
                Source: {hazards.thunderstorm.source} (Confidence: {hazards.thunderstorm.model_confidence * 100}%)
              </div>
            </div>
          )}

          {/* HAZARD 3: HEAVY RAINFALL & FLOOD RISK */}
          {hazards?.heavy_rainfall && (
            <div className="bg-white rounded-2xl border border-border-subtle p-5 shadow-card flex flex-col justify-between gap-4 md:col-span-2">
              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
                  <div className="flex items-center gap-2">
                    <CloudRain className="w-4 h-4 text-blue-600" />
                    <span className="font-bold text-xs text-ink-primary">3. Heavy Rainfall & Inundation Risk</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                      {hazards.heavy_rainfall.imd_category}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        hazards.heavy_rainfall.level === 3
                          ? "bg-red-600 text-white"
                          : hazards.heavy_rainfall.level === 2
                          ? "bg-orange-500 text-white"
                          : hazards.heavy_rainfall.level === 1
                          ? "bg-amber-400 text-slate-900"
                          : "bg-emerald-100 text-emerald-800"
                      }`}
                    >
                      Level {hazards.heavy_rainfall.level} • {hazards.heavy_rainfall.severity_label}
                    </span>
                  </div>
                </div>

                <div className="text-xs font-semibold text-ink-primary">
                  {hazards.heavy_rainfall.flood_status}
                </div>

                {/* Multi-Window Accumulation Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
                  {Object.entries(hazards.heavy_rainfall.accumulations_mm).map(([windowKey, mmVal]: [string, any]) => (
                    <div key={windowKey} className="p-2.5 rounded-xl bg-slate-50 border border-border-subtle flex flex-col items-center gap-0.5">
                      <span className="text-[10px] text-ink-muted uppercase font-bold">{windowKey} Rain</span>
                      <span className="text-base font-extrabold text-blue-700 tabular-nums">{mmVal} mm</span>
                    </div>
                  ))}
                </div>

                <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100 text-xs text-blue-950 flex flex-col gap-1">
                  <div className="font-bold">Floodplain & Basin Context:</div>
                  <div>{hazards.heavy_rainfall.floodplain_context}</div>
                  <div className="text-[11px] text-blue-800 pt-1">
                    <strong>Vulnerable Nodes:</strong> {hazards.heavy_rainfall.vulnerable_nodes.join(", ")}
                  </div>
                </div>

                {/* Safety Instructions */}
                <div className="flex flex-col gap-1 text-[11px]">
                  <span className="font-bold text-blue-950">Disaster Management Action Plan:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-ink-secondary">
                    {hazards.heavy_rainfall.instructions.map((ins: string, idx: number) => (
                      <li key={idx}>{ins}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="text-[10px] text-ink-muted pt-2 border-t border-border-subtle">
                Source: {hazards.heavy_rainfall.source} (Calibrated on IMD Criteria)
              </div>
            </div>
          )}

          {/* HAZARD 4: LANDSLIDE & SLOPE FAILURE RISK */}
          {hazards?.landslide && (
            <div className="bg-white rounded-2xl border border-border-subtle p-5 shadow-card flex flex-col justify-between gap-4">
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
                  <div className="flex items-center gap-2">
                    <Mountain className="w-4 h-4 text-emerald-700" />
                    <span className="font-bold text-xs text-ink-primary">4. Landslide & Slope Stability</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      hazards.landslide.level >= 2
                        ? "bg-red-100 text-red-800 border border-red-300"
                        : hazards.landslide.level === 1
                        ? "bg-amber-100 text-amber-800 border border-amber-300"
                        : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    Level {hazards.landslide.level} • {hazards.landslide.severity_label}
                  </span>
                </div>

                <div className="text-xs font-semibold text-ink-primary">
                  {hazards.landslide.status}
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-border-subtle text-[11px] flex flex-col gap-1.5">
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">Geotechnical Relief Category:</span>
                    <span className="font-semibold text-ink-primary">{hazards.landslide.susceptibility_category}</span>
                  </div>
                  {hazards.landslide.antecedent_moisture_mm && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-ink-secondary">72h Antecedent Rain:</span>
                        <span className="font-bold">{hazards.landslide.antecedent_moisture_mm.antecedent_72h} mm</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-ink-secondary">Empirical Trigger Threshold:</span>
                        <span className="text-red-700 font-bold">{hazards.landslide.antecedent_moisture_mm.empirical_trigger_threshold} mm</span>
                      </div>
                    </>
                  )}
                </div>

                {hazards.landslide.critical_ghats && (
                  <div className="p-2.5 rounded-lg bg-amber-50/70 border border-amber-200 text-[11px] text-amber-950 flex flex-col gap-1">
                    <span className="font-bold">Critical Ghat Corridors Monitored:</span>
                    <span>{hazards.landslide.critical_ghats.join("; ")}</span>
                  </div>
                )}

                {/* Safety Instructions */}
                <div className="flex flex-col gap-1 text-[11px]">
                  <span className="font-bold text-ink-primary">Slope Safety Advisories:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-ink-secondary">
                    {hazards.landslide.instructions.map((ins: string, idx: number) => (
                      <li key={idx}>{ins}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="text-[10px] text-ink-muted pt-2 border-t border-border-subtle">
                Source: {hazards.landslide.source}
              </div>
            </div>
          )}

          {/* HAZARD 5: TSUNAMI & MARINE COASTAL SURGE (INCOIS AUTHORITATIVE ONLY) */}
          {hazards?.tsunami && (
            <div className="bg-white rounded-2xl border border-border-subtle p-5 shadow-card flex flex-col justify-between gap-4">
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
                  <div className="flex items-center gap-2">
                    <Waves className="w-4 h-4 text-purple-600" />
                    <span className="font-bold text-xs text-ink-primary">5. Tsunami & Coastal Marine Surge</span>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      hazards.tsunami.level >= 2
                        ? "bg-red-600 text-white animate-pulse"
                        : "bg-slate-100 text-slate-700"
                    }`}
                  >
                    Level {hazards.tsunami.level} • {hazards.tsunami.severity_label}
                  </span>
                </div>

                <div className="text-xs font-semibold text-ink-primary">
                  {hazards.tsunami.status}
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-border-subtle text-[11px] flex flex-col gap-1.5">
                  <div className="flex justify-between">
                    <span className="text-ink-secondary">Coastal Geography:</span>
                    <span className="font-semibold text-ink-primary">
                      {hazards.tsunami.is_coastal ? "Vulnerable Coastline" : "Inland Elevation (Safe)"}
                    </span>
                  </div>
                  {hazards.tsunami.coastal_zone && (
                    <div className="flex justify-between">
                      <span className="text-ink-secondary">INCOIS Coastal Zone:</span>
                      <span className="font-semibold">{hazards.tsunami.coastal_zone}</span>
                    </div>
                  )}
                  {hazards.tsunami.official_bulletin_id && (
                    <div className="flex justify-between">
                      <span className="text-ink-secondary">Official Bulletin ID:</span>
                      <span className="font-bold text-red-600">{hazards.tsunami.official_bulletin_id}</span>
                    </div>
                  )}
                </div>

                {/* Safety Instructions */}
                <div className="flex flex-col gap-1 text-[11px]">
                  <span className="font-bold text-purple-950">Coastal Directives:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-ink-secondary">
                    {hazards.tsunami.instructions.map((ins: string, idx: number) => (
                      <li key={idx}>{ins}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* CRITICAL TSUNAMI DESIGN PRINCIPLE CALLOUT */}
              <div className="p-2.5 rounded-lg bg-purple-50/70 border border-purple-200 text-[10px] text-purple-900 leading-relaxed">
                <strong>Mandatory Constraint:</strong> Tsunami alerts are tied directly to authorized INCOIS bulletins. A.L.Y.A strictly prohibits generating independent synthetic ML models for tsunami predictions.
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 5. MULTI-CHANNEL DISPATCH SIMULATOR & DUPLICATE SUPPRESSION */}
      <div className="bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col gap-4">
        <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
          <div className="flex items-center gap-2">
            <Send className="w-4 h-4 text-brand-sky" />
            <h4 className="text-sm font-bold text-ink-primary">
              Multi-Channel Alert Dispatch Simulator & Duplicate Suppression Engine
            </h4>
          </div>
          <span className="text-xs text-ink-muted">Anti-Flapping Filter Active</span>
        </div>

        <p className="text-xs text-ink-secondary leading-relaxed">
          Demonstrates simultaneous delivery to <strong>In-App Dashboard, Web Push, SMS, and Email</strong> with intelligent duplicate suppression (prevents user spam for identical ongoing hazards).
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div className="flex flex-col gap-1">
            <label className="font-semibold text-ink-primary">Hazard Type:</label>
            <select
              value={dispatchHazard}
              onChange={(e) => setDispatchHazard(e.target.value)}
              className="bg-canvas-subtle border border-border-subtle rounded-lg px-2.5 py-1.5"
            >
              <option value="heavy_rainfall">Heavy Rainfall & Flood</option>
              <option value="lightning">Lightning & Thunderstorm</option>
              <option value="landslide">Landslide & Slope Failure</option>
              <option value="tsunami">Tsunami Warning (INCOIS)</option>
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-semibold text-ink-primary">Alert Level:</label>
            <select
              value={dispatchLevel}
              onChange={(e) => setDispatchLevel(parseInt(e.target.value))}
              className="bg-canvas-subtle border border-border-subtle rounded-lg px-2.5 py-1.5"
            >
              <option value={1}>Level 1 — Watch</option>
              <option value={2}>Level 2 — Warning</option>
              <option value={3}>Level 3 — Emergency</option>
            </select>
          </div>

          <div className="flex flex-col gap-1 sm:col-span-2">
            <label className="font-semibold text-ink-primary">Alert Broadcast Headline:</label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={dispatchHeadline}
                onChange={(e) => setDispatchHeadline(e.target.value)}
                className="bg-canvas-subtle border border-border-subtle rounded-lg px-2.5 py-1.5 w-full text-xs"
              />
              <button
                onClick={handleDispatch}
                className="px-4 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-xs shrink-0 flex items-center gap-1.5 shadow-xs"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Dispatch</span>
              </button>
            </div>
          </div>
        </div>

        {/* Dispatch Result Feedback */}
        {dispatchStatus && (
          <div
            className={`p-4 rounded-xl border text-xs flex flex-col gap-2 ${
              dispatchStatus.suppressed
                ? "bg-amber-50 border-amber-300 text-amber-950"
                : "bg-emerald-50 border-emerald-300 text-emerald-950"
            }`}
          >
            <div className="flex items-center justify-between font-bold">
              <span className="flex items-center gap-1.5">
                {dispatchStatus.suppressed ? (
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                )}
                {dispatchStatus.suppressed
                  ? "DUPLICATE ALERT SUPPRESSED"
                  : `ALERT SUCCESSFULLY DISPATCHED (${dispatchStatus.dispatch_id ? dispatchStatus.dispatch_id.slice(0, 8) : "OK"})`}
              </span>
              <span className="text-[10px] opacity-80">{dispatchStatus.dispatched_at}</span>
            </div>

            {dispatchStatus.suppressed && (
              <p className="text-[11px] leading-relaxed">
                {dispatchStatus.suppression_reason}
              </p>
            )}

            {!dispatchStatus.suppressed && dispatchStatus.channel_payloads && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-black/5 text-[11px]">
                <div className="p-2 rounded bg-white/70 border border-slate-200">
                  <span className="font-bold flex items-center gap-1 text-slate-700">
                    <Smartphone className="w-3 h-3" /> Web Push:
                  </span>
                  <div className="text-[10px] text-slate-600 mt-0.5">
                    {dispatchStatus.channel_payloads.push.title}
                  </div>
                </div>

                <div className="p-2 rounded bg-white/70 border border-slate-200">
                  <span className="font-bold flex items-center gap-1 text-slate-700">
                    <Radio className="w-3 h-3" /> SMS Broadcast:
                  </span>
                  <div className="text-[10px] text-slate-600 mt-0.5">
                    {dispatchStatus.channel_payloads.sms.text}
                  </div>
                </div>

                <div className="p-2 rounded bg-white/70 border border-slate-200">
                  <span className="font-bold flex items-center gap-1 text-slate-700">
                    <Mail className="w-3 h-3" /> Email Incident:
                  </span>
                  <div className="text-[10px] text-slate-600 mt-0.5">
                    {dispatchStatus.channel_payloads.email.subject}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 6. INTERACTIVE SENSITIVITY & STRESS-TEST SANDBOX */}
      {isSimulating && (
        <div className="bg-white rounded-2xl border border-amber-300 p-6 shadow-card flex flex-col gap-4 animate-in fade-in duration-200">
          <div className="flex items-center gap-2 pb-2 border-b border-border-subtle">
            <Sliders className="w-4 h-4 text-amber-600" />
            <h4 className="text-sm font-bold text-ink-primary">
              Interactive Stress-Test Sandbox (Simulating Catastrophic Meteorological Conditions)
            </h4>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
            {/* 24h Rain */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between">
                <span className="font-semibold text-ink-primary">24h Rainfall:</span>
                <span className="font-bold text-blue-700">{simPrecip24h} mm</span>
              </div>
              <input
                type="range"
                min="0"
                max="300"
                step="5"
                value={simPrecip24h}
                onChange={(e) => setSimPrecip24h(parseFloat(e.target.value))}
                className="accent-blue-600 cursor-pointer"
              />
              <span className="text-[10px] text-ink-muted">Red Alert Threshold: &gt;204.4 mm</span>
            </div>

            {/* Wind Gust */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between">
                <span className="font-semibold text-ink-primary">Peak Wind Gust:</span>
                <span className="font-bold text-sky-700">{simWindGust} km/h</span>
              </div>
              <input
                type="range"
                min="10"
                max="120"
                step="5"
                value={simWindGust}
                onChange={(e) => setSimWindGust(parseFloat(e.target.value))}
                className="accent-sky-600 cursor-pointer"
              />
              <span className="text-[10px] text-ink-muted">Squall Warning: &gt;50 km/h</span>
            </div>

            {/* Antecedent Rain */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between">
                <span className="font-semibold text-ink-primary">72h Antecedent Rain:</span>
                <span className="font-bold text-emerald-700">{simAntecedent72h} mm</span>
              </div>
              <input
                type="range"
                min="0"
                max="250"
                step="5"
                value={simAntecedent72h}
                onChange={(e) => setSimAntecedent72h(parseFloat(e.target.value))}
                className="accent-emerald-600 cursor-pointer"
              />
              <span className="text-[10px] text-ink-muted">Nilgiris Ghat Trigger: 150 mm</span>
            </div>

            {/* Tsunami Toggle */}
            <div className="flex flex-col justify-between p-2.5 rounded-xl bg-purple-50/60 border border-purple-200">
              <div className="flex items-center justify-between">
                <span className="font-bold text-purple-900 text-[11px]">Simulate INCOIS Tsunami Warning:</span>
                <input
                  type="checkbox"
                  checked={simTsunamiActive}
                  onChange={(e) => setSimTsunamiActive(e.target.checked)}
                  className="accent-purple-600 w-4 h-4 cursor-pointer"
                />
              </div>
              <span className="text-[10px] text-purple-800">
                Tests coastal vs inland district evacuation behavior.
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 7. STATEWIDE TAMIL NADU SITUATIONAL RADAR MATRIX */}
      {regionalData && regionalData.items && (
        <div className="bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col gap-4">
          <div className="flex items-center justify-between pb-2 border-b border-border-subtle">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-brand-sky" />
              <h4 className="text-sm font-bold text-ink-primary">
                Tamil Nadu Multi-District Situational Matrix (TNSDMA State Coordination)
              </h4>
            </div>
            <span className="text-xs text-ink-muted">
              {regionalData.district_count} Monitored Districts
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {regionalData.items.map((item: any) => {
              const isCurrent = activeLocId === item.location_id;
              return (
                <div
                  key={item.location_id}
                  onClick={() => {
                    if (onSelectLocation) {
                      onSelectLocation(item.location_id);
                    }
                  }}
                  className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between gap-2 ${
                    isCurrent
                      ? "bg-slate-50 border-brand-deepTeal shadow-sm ring-1 ring-brand-deepTeal"
                      : "bg-white border-border-subtle hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-ink-primary">{item.name}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                        item.overall_alert.level === 3
                          ? "bg-red-600 text-white"
                          : item.overall_alert.level === 2
                          ? "bg-orange-500 text-white"
                          : item.overall_alert.level === 1
                          ? "bg-amber-400 text-slate-900"
                          : "bg-emerald-100 text-emerald-800"
                      }`}
                    >
                      L{item.overall_alert.level}
                    </span>
                  </div>

                  <div className="text-[11px] text-ink-secondary truncate">
                    Threat: <span className="font-semibold text-ink-primary">{item.top_threat}</span>
                  </div>

                  <div className="flex items-center gap-1.5 text-[10px] text-ink-muted pt-1 border-t border-border-subtle">
                    {item.is_coastal && (
                      <span className="px-1.5 py-0.2 bg-blue-50 text-blue-700 rounded border border-blue-200">
                        Coastal
                      </span>
                    )}
                    {item.is_mountainous && (
                      <span className="px-1.5 py-0.2 bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
                        Ghats / Slopes
                      </span>
                    )}
                    {!item.is_coastal && !item.is_mountainous && (
                      <span className="px-1.5 py-0.2 bg-slate-50 text-slate-600 rounded">
                        Plains
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
