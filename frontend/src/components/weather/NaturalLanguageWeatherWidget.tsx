"use client";

import React, { useState } from "react";
import { Sparkles, Send, RefreshCw, HelpCircle, Database, CheckCircle2 } from "lucide-react";
import { queryNaturalLanguageWeather, NLPWeatherQueryResponse } from "../../lib/api";
import { LocationData } from "../../types";

interface NaturalLanguageWeatherWidgetProps {
  location: LocationData | null;
  currentTemp?: number | null;
  dailyPrecip?: number | null;
}

export function NaturalLanguageWeatherWidget({
  location,
  currentTemp,
  dailyPrecip,
}: NaturalLanguageWeatherWidgetProps) {
  const [queryText, setQueryText] = useState<string>("What is the probability of heavy rain in Chennai tomorrow?");
  const [response, setResponse] = useState<NLPWeatherQueryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const locId = location?.id || "chennai";
  const locName = location?.name || "Chennai";

  const handleQuery = async (textToRun?: string) => {
    const q = textToRun || queryText;
    if (!q.trim()) return;
    setIsLoading(true);
    try {
      const res = await queryNaturalLanguageWeather({
        query: q,
        locationId: locId,
        currentTemp: currentTemp ?? 31.5,
        dailyRainMm: dailyPrecip ?? 18.4,
        maxRainProb: 68,
      });
      setResponse(res);
    } catch (err) {
      console.error("Natural language weather query failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-border-subtle p-5 shadow-card flex flex-col gap-4 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center shrink-0">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wide">
              Natural-Language Weather Intelligence
            </h3>
            <p className="text-[11px] text-ink-secondary">
              Ask meteorological questions for {locName} grounded in ECMWF & ERA5 observational data.
            </p>
          </div>
        </div>
        <span className="text-[10px] font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 self-start sm:self-auto">
          Observation-Grounded LLM Layer
        </span>
      </div>

      {/* Suggested Query Chips */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className="text-[10px] text-ink-muted font-medium">Quick Queries:</span>
        {[
          `What is the probability of heavy rain in ${locName} tomorrow?`,
          `Why is ${locName} warmer than its surroundings?`,
          "Compare this monsoon season with historical averages.",
          "Which districts have the highest predicted rainfall risk?",
        ].map((chip, idx) => (
          <button
            key={idx}
            onClick={() => {
              setQueryText(chip);
              handleQuery(chip);
            }}
            className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-sky-50 text-ink-secondary hover:text-sky-900 border border-border-subtle hover:border-sky-200 transition-all text-left"
          >
            "{chip}"
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleQuery();
          }}
          placeholder="Ask about rainfall probability, microclimates, thermal anomalies..."
          className="flex-1 rounded-xl border border-border-subtle bg-slate-50/60 px-3.5 py-2 text-xs text-ink-primary placeholder:text-ink-muted focus:outline-hidden focus:border-sky-500 focus:bg-white transition-all"
        />
        <button
          onClick={() => handleQuery()}
          disabled={isLoading || !queryText.trim()}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold transition-all shadow-xs shrink-0 disabled:opacity-50"
        >
          {isLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
          <span>Ask</span>
        </button>
      </div>

      {/* Structured Grounded Response */}
      {response && (
        <div className="p-4 rounded-xl bg-gradient-to-br from-sky-50/40 via-white to-slate-50 border border-sky-100 flex flex-col gap-3 text-xs animate-in slide-in-from-top-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-sky-950 uppercase tracking-wide flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Verified Meteorological Synthesis
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-sky-100 text-sky-800 font-semibold">
              Intent: {response.intent}
            </span>
          </div>

          <p className="text-ink-primary font-medium leading-relaxed">
            {response.answer}
          </p>

          {/* Quantitative Data Points */}
          {response.data_points && Object.keys(response.data_points).length > 0 && (
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex flex-wrap items-center gap-3 text-[11px]">
              {Object.entries(response.data_points).map(([k, v]) => (
                <div key={k} className="flex flex-col">
                  <span className="text-[9px] text-ink-muted uppercase">{k.replace(/_/g, " ")}:</span>
                  <strong className="text-sky-900 font-mono">
                    {typeof v === "object" ? JSON.stringify(v).slice(0, 30) + "..." : String(v)}
                  </strong>
                </div>
              ))}
            </div>
          )}

          {/* Provenance and Uncertainty Footer */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-slate-200/60 text-[10px] text-ink-muted">
            <div className="flex items-center gap-1">
              <Database className="w-3 h-3 text-sky-600 shrink-0" />
              <span>Data Provenance: <strong className="text-slate-700">{response.data_provenance}</strong></span>
            </div>
            <div className="flex items-center gap-1">
              <HelpCircle className="w-3 h-3 text-amber-600 shrink-0" />
              <span>Uncertainty: <strong className="text-slate-700">{response.uncertainty_explanation}</strong></span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
