"use client";

import React, { useState } from "react";
import { X, Copy, Check, Download, Sparkles, Wind, Sun, Droplets } from "lucide-react";
import { LocationData, CurrentConditions } from "../../types";
import { WeatherStoryData } from "../../lib/intelligence";

interface ShareableWeatherCardProps {
  isOpen: boolean;
  onClose: () => void;
  location: LocationData | null;
  current: CurrentConditions | null;
  story: WeatherStoryData | null;
}

export function ShareableWeatherCard({
  isOpen,
  onClose,
  location,
  current,
  story,
}: ShareableWeatherCardProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const currentTemp = current?.values?.temperature_2m ?? 28;
  const shareText = `☀️ A.L.Y.A Weather — ${location?.name || "Chennai"}, ${location?.state || "India"}
🌡️ ${currentTemp}°C • "${story?.headline || "Clear skies and moderate warmth"}"
📖 ${story?.narrative || ""}
💨 Lyrical forecasts & air quality intelligence for India.`;

  const handleCopy = () => {
    navigator.clipboard.writeText(shareText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-white rounded-3xl border border-border-subtle shadow-2xl p-6 sm:p-7 flex flex-col gap-5 overflow-hidden">
        {/* Modal Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-full hover:bg-canvas-subtle text-ink-muted hover:text-ink-primary transition-all z-10"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Shareable Card Visual Content */}
        <div className="relative rounded-2xl p-6 bg-gradient-to-br from-brand-aquaLight via-white to-brand-peach/30 border border-brand-aqua/30 shadow-sm flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-brand-aqua/20 pb-3">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-base tracking-tight text-ink-primary font-serif">
                A.L.Y.A
              </span>
              <span className="text-[9px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded bg-brand-deepTeal text-white">
                India
              </span>
            </div>
            <span className="text-[11px] text-ink-secondary">
              {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
            </span>
          </div>

          <div>
            <div className="text-xs uppercase font-bold text-brand-deepTeal tracking-wider">
              {location?.name || "Chennai"}, {location?.state || "Tamil Nadu"}
            </div>
            <div className="text-5xl font-light text-ink-primary font-mono tabular-nums tracking-tighter my-1">
              {currentTemp}°C
            </div>
            <div className="text-sm font-semibold text-ink-primary">
              "{story?.headline || "Clear and pleasant morning"}"
            </div>
          </div>

          <p className="text-xs text-ink-secondary italic leading-relaxed bg-white/70 backdrop-blur-xs p-3 rounded-xl border border-border-subtle/60">
            "{story?.narrative || "Gentle sunlight warms the waking day."}"
          </p>

          <div className="flex items-center justify-between text-[11px] text-ink-muted pt-2 border-t border-brand-aqua/20">
            <span>The sky, simplified.</span>
            <span className="font-mono text-brand-sky">alyaclimate.in</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2.5 pt-1">
          <button
            onClick={handleCopy}
            className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl border border-border-subtle bg-canvas-subtle hover:bg-canvas-subtle/80 text-ink-primary text-xs font-semibold transition-all"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copied to Clipboard!" : "Copy Forecast Text"}</span>
          </button>

          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-brand-sky hover:bg-brand-sky/90 text-white text-xs font-bold transition-all"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
export default ShareableWeatherCard;
