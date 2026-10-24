"use client";

import React, { useState } from "react";
import { Search, MapPin, Sparkles, SlidersHorizontal, Check } from "lucide-react";
import { LocationData } from "../../types";
import { TemperatureUnit } from "../../lib/units";

interface HeaderProps {
  currentLocation: LocationData | null;
  temperatureUnit: TemperatureUnit;
  onToggleUnit: () => void;
  onOpenSearch: () => void;
  onOpenSettings: () => void;
  isBackendHealthy: boolean | null;
}

export function Header({
  currentLocation,
  temperatureUnit,
  onToggleUnit,
  onOpenSearch,
  onOpenSettings,
  isBackendHealthy,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-border-subtle px-4 lg:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-aquaLight border border-brand-aqua/30 flex items-center justify-center p-1 shadow-sm overflow-hidden group">
            <img
              src="/logo.png"
              alt="A.L.Y.A Logo"
              className="w-full h-full object-contain group-hover:scale-110 transition-transform duration-300"
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-ink-primary tracking-wide font-serif">
                A.L.Y.A
              </h1>
              <span className="hidden sm:inline-flex text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-brand-aquaLight text-brand-deepTeal border border-brand-aqua/30">
                India
              </span>
            </div>
            <p className="text-xs text-ink-secondary hidden sm:block">
              Lyrical Forecasts & Air Quality
            </p>
          </div>
        </div>

        {/* Center: Location Quick Pill */}
        <button
          onClick={onOpenSearch}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-canvas-subtle hover:bg-slate-100 border border-border-subtle hover:border-border-strong text-ink-primary transition-all text-xs sm:text-sm group max-w-[240px] sm:max-w-xs truncate"
          title="Search Indian cities, districts, and states"
        >
          <MapPin className="w-3.5 h-3.5 text-brand-sky shrink-0 group-hover:scale-110 transition-transform" />
          <span className="font-medium truncate">
            {currentLocation ? (
              <>
                {currentLocation.name || "Selected Location"}
                {currentLocation.state ? `, ${currentLocation.state}` : ""}
              </>
            ) : (
              "Select Location..."
            )}
          </span>
          <Search className="w-3 h-3 text-ink-muted ml-1 shrink-0" />
        </button>

        {/* Right Actions: Unit switch, Backend indicator, Settings */}
        <div className="flex items-center gap-2">
          {/* Temperature unit switch */}
          <button
            onClick={onToggleUnit}
            className="flex items-center bg-canvas-subtle border border-border-subtle rounded-lg p-1 text-xs font-semibold text-ink-secondary hover:text-ink-primary transition-colors"
            title={`Switch to °${temperatureUnit === "C" ? "F" : "C"}`}
          >
            <span
              className={`px-2 py-0.5 rounded ${
                temperatureUnit === "C"
                  ? "bg-white text-brand-sky shadow-sm"
                  : "text-ink-muted"
              }`}
            >
              °C
            </span>
            <span
              className={`px-2 py-0.5 rounded ${
                temperatureUnit === "F"
                  ? "bg-white text-brand-sky shadow-sm"
                  : "text-ink-muted"
              }`}
            >
              °F
            </span>
          </button>

          {/* Backend Status indicator */}
          <div
            className="hidden md:flex items-center gap-1.5 text-[11px] font-medium text-ink-secondary px-2.5 py-1 rounded-md bg-canvas-subtle border border-border-subtle"
            title={
              isBackendHealthy === true
                ? "Backend API Connected (FastAPI v1)"
                : isBackendHealthy === false
                ? "Backend Offline or Unreachable"
                : "Connecting to Backend..."
            }
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendHealthy === true
                  ? "bg-emerald-500 animate-pulse"
                  : isBackendHealthy === false
                  ? "bg-rose-500"
                  : "bg-amber-400"
              }`}
            />
            <span className="text-[11px]">
              {isBackendHealthy === true ? "Live API" : "Offline"}
            </span>
          </div>

          {/* Settings button */}
          <button
            onClick={onOpenSettings}
            className="p-2 rounded-lg text-ink-secondary hover:text-ink-primary hover:bg-canvas-subtle border border-border-subtle transition-colors"
            title="Settings & Preferences"
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
