"use client";

import React from "react";
import { X, Sliders, Trash2, MapPin } from "lucide-react";
import { UserPreferences } from "../../lib/storage";
import { TemperatureUnit, WindSpeedUnit, PrecipitationUnit } from "../../lib/units";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  preferences: UserPreferences;
  onUpdatePreferences: (updated: Partial<UserPreferences>) => void;
  favoriteLocations: Array<{ id: string; name: string; state: string }>;
  onSelectLocationId: (id: string) => void;
  onRemoveFavorite: (id: string) => void;
}

export function SettingsModal({
  isOpen,
  onClose,
  preferences,
  onUpdatePreferences,
  favoriteLocations,
  onSelectLocationId,
  onRemoveFavorite,
}: SettingsModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/30 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-lg bg-white rounded-2xl border border-border-strong shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-border-subtle flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-brand-sky" />
            <h3 className="text-base font-bold text-ink-primary">
              Preferences & Units
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-ink-secondary hover:bg-canvas-subtle"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 flex flex-col gap-6 overflow-y-auto custom-scrollbar">
          {/* Temperature Unit */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-semibold text-ink-primary block">
                Temperature Unit
              </span>
              <span className="text-xs text-ink-secondary">
                Display temperatures in Celsius or Fahrenheit
              </span>
            </div>
            <div className="flex items-center bg-canvas-subtle p-1 rounded-lg border border-border-subtle text-xs">
              {(["C", "F"] as TemperatureUnit[]).map((unit) => (
                <button
                  key={unit}
                  onClick={() => onUpdatePreferences({ temperatureUnit: unit })}
                  className={`px-3 py-1 rounded font-medium transition-all ${
                    preferences.temperatureUnit === unit
                      ? "bg-white text-brand-sky shadow-sm font-bold"
                      : "text-ink-secondary hover:text-ink-primary"
                  }`}
                >
                  °{unit}
                </button>
              ))}
            </div>
          </div>

          {/* Wind Speed Unit */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-semibold text-ink-primary block">
                Wind Speed Unit
              </span>
              <span className="text-xs text-ink-secondary">
                Velocity measurements format
              </span>
            </div>
            <div className="flex items-center bg-canvas-subtle p-1 rounded-lg border border-border-subtle text-xs">
              {(["km/h", "m/s", "mph"] as WindSpeedUnit[]).map((unit) => (
                <button
                  key={unit}
                  onClick={() => onUpdatePreferences({ windSpeedUnit: unit })}
                  className={`px-2.5 py-1 rounded font-medium transition-all ${
                    preferences.windSpeedUnit === unit
                      ? "bg-white text-brand-sky shadow-sm font-bold"
                      : "text-ink-secondary hover:text-ink-primary"
                  }`}
                >
                  {unit}
                </button>
              ))}
            </div>
          </div>

          {/* Precipitation Unit */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-semibold text-ink-primary block">
                Precipitation Volume
              </span>
              <span className="text-xs text-ink-secondary">
                Rainfall volume accumulation units
              </span>
            </div>
            <div className="flex items-center bg-canvas-subtle p-1 rounded-lg border border-border-subtle text-xs">
              {(["mm", "in"] as PrecipitationUnit[]).map((unit) => (
                <button
                  key={unit}
                  onClick={() => onUpdatePreferences({ precipitationUnit: unit })}
                  className={`px-3 py-1 rounded font-medium transition-all ${
                    preferences.precipitationUnit === unit
                      ? "bg-white text-brand-sky shadow-sm font-bold"
                      : "text-ink-secondary hover:text-ink-primary"
                  }`}
                >
                  {unit}
                </button>
              ))}
            </div>
          </div>

          {/* Time Format */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-semibold text-ink-primary block">
                Time Format
              </span>
              <span className="text-xs text-ink-secondary">
                Clock display format
              </span>
            </div>
            <div className="flex items-center bg-canvas-subtle p-1 rounded-lg border border-border-subtle text-xs">
              <button
                onClick={() => onUpdatePreferences({ is24Hour: false })}
                className={`px-3 py-1 rounded font-medium transition-all ${
                  !preferences.is24Hour
                    ? "bg-white text-brand-sky shadow-sm font-bold"
                    : "text-ink-secondary hover:text-ink-primary"
                }`}
              >
                12-Hour (AM/PM)
              </button>
              <button
                onClick={() => onUpdatePreferences({ is24Hour: true })}
                className={`px-3 py-1 rounded font-medium transition-all ${
                  preferences.is24Hour
                    ? "bg-white text-brand-sky shadow-sm font-bold"
                    : "text-ink-secondary hover:text-ink-primary"
                }`}
              >
                24-Hour
              </button>
            </div>
          </div>

          {/* Favorite Locations List */}
          <div className="pt-4 border-t border-border-subtle">
            <span className="text-sm font-semibold text-ink-primary block mb-2">
              Bookmarked Locations ({favoriteLocations.length})
            </span>
            <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto custom-scrollbar">
              {favoriteLocations.length === 0 ? (
                <span className="text-xs text-ink-muted italic">
                  No bookmarked locations yet. Search and click the star icon to save favorites.
                </span>
              ) : (
                favoriteLocations.map((fav) => (
                  <div
                    key={fav.id}
                    className="p-2.5 rounded-xl bg-canvas-subtle border border-border-subtle flex items-center justify-between text-xs"
                  >
                    <button
                      onClick={() => {
                        onSelectLocationId(fav.id);
                        onClose();
                      }}
                      className="flex items-center gap-2 font-medium text-ink-primary hover:text-brand-sky truncate flex-1 text-left"
                    >
                      <MapPin className="w-3.5 h-3.5 text-brand-sky shrink-0" />
                      <span className="truncate">
                        {fav.name}, {fav.state}
                      </span>
                    </button>
                    <button
                      onClick={() => onRemoveFavorite(fav.id)}
                      className="text-ink-muted hover:text-rose-500 p-1"
                      title="Remove bookmark"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-canvas-subtle border-t border-border-subtle flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-brand-sky text-white rounded-xl text-xs font-semibold hover:bg-sky-600 transition-colors shadow-sm"
          >
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
}
