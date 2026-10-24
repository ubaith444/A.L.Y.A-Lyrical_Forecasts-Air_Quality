"use client";

import React, { useEffect, useState } from "react";
import { Info, ExternalLink, ShieldCheck, Database, Cpu } from "lucide-react";
import { DataSourceItem } from "../../types";
import { fetchDataSources, fetchEvaluations } from "../../lib/api";

export function SourcesModal() {
  const [sources, setSources] = useState<DataSourceItem[]>([]);
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [srcRes, evalRes] = await Promise.allSettled([
          fetchDataSources(),
          fetchEvaluations(),
        ]);
        if (srcRes.status === "fulfilled") setSources(srcRes.value.items || []);
        if (evalRes.status === "fulfilled") setEvaluations(evalRes.value.items || []);
      } catch (err) {
        console.error("Failed to load sources:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="w-full bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col gap-6">
      {/* Header */}
      <div className="pb-4 border-b border-border-subtle">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-brand-sky" />
          <h3 className="text-base font-bold text-ink-primary">
            Data Sources, Provenance & Scientific Methodology
          </h3>
        </div>
        <p className="text-xs text-ink-secondary mt-1">
          Honest disclosure of model forecasts, atmospheric reanalysis, and evaluation baselines.
        </p>
      </div>

      {/* Grid of Data Providers */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sources.map((src) => (
          <div
            key={src.id}
            className="p-4 rounded-xl bg-canvas-subtle/80 border border-border-subtle flex flex-col justify-between gap-3 text-xs"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-bold text-sm text-ink-primary">
                  {src.name}
                </span>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-white text-brand-sky border border-border-subtle">
                  {src.kind.replace("_", " ")}
                </span>
              </div>
              <p className="text-ink-secondary text-[11px] mt-2 leading-relaxed">
                <strong>Limitations & Grid Approximation:</strong> {src.limitations}
              </p>
            </div>

            <a
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[11px] text-brand-sky hover:underline font-medium pt-2 border-t border-border-subtle/70"
            >
              <span>Provider Documentation</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        ))}
      </div>

      {/* Model & Persistence Baseline Transparency Section */}
      <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 text-xs flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-brand-sky" />
          <h4 className="font-bold text-ink-primary text-sm">
            Ethical AI & Baseline Evaluation Standards
          </h4>
        </div>
        <p className="text-ink-secondary leading-relaxed">
          Alya Weather adheres to strict scientific integrity: we do not claim artificial intelligence or train deep learning models merely for marketing claims. A reproducible chronological persistence baseline is maintained and benchmarked before any predictive model can ever be considered for deployment.
        </p>

        {evaluations.length > 0 && (
          <div className="mt-2 p-3 bg-white rounded-lg border border-border-subtle flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <span className="font-semibold text-ink-primary">
                Active Benchmark: Persistence Baseline
              </span>
              <p className="text-[11px] text-ink-muted">
                MAE: {evaluations[0]?.metrics?.mae ?? "—"} • RMSE: {evaluations[0]?.metrics?.rmse ?? "—"}
              </p>
            </div>
            <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 shrink-0">
              Validated Baseline
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
