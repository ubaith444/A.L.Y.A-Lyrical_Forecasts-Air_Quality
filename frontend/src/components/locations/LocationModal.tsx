"use client";

import React, { useState, useEffect, useTransition } from "react";
import {
  Search,
  X,
  MapPin,
  Star,
  Check,
  Building2,
  Landmark,
  Compass,
} from "lucide-react";
import { LocationData, StateRecord } from "../../types";
import { fetchLocations, fetchStates } from "../../lib/api";

interface LocationModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentLocationId: string | null;
  onSelectLocation: (location: LocationData) => void;
  favorites: string[];
  onToggleFavorite: (locationId: string) => void;
}

export function LocationModal({
  isOpen,
  onClose,
  currentLocationId,
  onSelectLocation,
  favorites,
  onToggleFavorite,
}: LocationModalProps) {
  const [query, setQuery] = useState("");
  const [selectedState, setSelectedState] = useState<string>("");
  const [selectedType, setSelectedType] = useState<string>("");
  const [results, setResults] = useState<LocationData[]>([]);
  const [statesList, setStatesList] = useState<StateRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load available states once
  useEffect(() => {
    async function loadStates() {
      try {
        const res = await fetchStates();
        setStatesList(res.items || []);
      } catch (err) {
        console.error("Failed to load states:", err);
      }
    }
    loadStates();
  }, []);

  // Live search debounced
  useEffect(() => {
    if (!isOpen) return;
    const timeout = setTimeout(async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await fetchLocations({
          query: query.trim() || undefined,
          state: selectedState || undefined,
          type: selectedType || undefined,
          limit: 30,
        });
        setResults(res.items || []);
      } catch (err: any) {
        setError(err.message || "Search failed");
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timeout);
  }, [isOpen, query, selectedState, selectedType]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/30 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-2xl bg-white rounded-2xl border border-border-strong shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Search Header */}
        <div className="p-4 sm:p-5 border-b border-border-subtle flex items-center gap-3">
          <Search className="w-5 h-5 text-ink-muted shrink-0" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search Indian cities, districts, states (e.g. Chennai, Ooty, Delhi)..."
            className="flex-1 bg-transparent text-sm sm:text-base font-medium text-ink-primary placeholder:text-ink-muted outline-none"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="p-1 text-ink-muted hover:text-ink-primary"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-ink-secondary hover:bg-canvas-subtle"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Filter Bar */}
        <div className="px-4 py-2.5 bg-canvas-subtle border-b border-border-subtle flex items-center gap-2 overflow-x-auto custom-scrollbar text-xs">
          {/* Priority Quick Filter: Tamil Nadu */}
          <button
            onClick={() =>
              setSelectedState((prev) => (prev === "Tamil Nadu" ? "" : "Tamil Nadu"))
            }
            className={`px-3 py-1 rounded-full font-semibold border transition-all ${
              selectedState === "Tamil Nadu"
                ? "bg-brand-sky text-white border-brand-sky"
                : "bg-white text-ink-secondary border-border-subtle hover:border-brand-sky"
            }`}
          >
            Tamil Nadu
          </button>

          {/* Type Filters */}
          <button
            onClick={() => setSelectedType((prev) => (prev === "city" ? "" : "city"))}
            className={`px-3 py-1 rounded-full border transition-all ${
              selectedType === "city"
                ? "bg-brand-sky text-white border-brand-sky font-semibold"
                : "bg-white text-ink-secondary border-border-subtle hover:border-border-strong"
            }`}
          >
            Cities
          </button>

          <button
            onClick={() =>
              setSelectedType((prev) => (prev === "district" ? "" : "district"))
            }
            className={`px-3 py-1 rounded-full border transition-all ${
              selectedType === "district"
                ? "bg-brand-sky text-white border-brand-sky font-semibold"
                : "bg-white text-ink-secondary border-border-subtle hover:border-border-strong"
            }`}
          >
            Districts
          </button>

          <button
            onClick={() => setSelectedType((prev) => (prev === "state" ? "" : "state"))}
            className={`px-3 py-1 rounded-full border transition-all ${
              selectedType === "state"
                ? "bg-brand-sky text-white border-brand-sky font-semibold"
                : "bg-white text-ink-secondary border-border-subtle hover:border-border-strong"
            }`}
          >
            States / UTs
          </button>

          {/* State selector dropdown */}
          <select
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="px-2.5 py-1 rounded-full bg-white border border-border-subtle text-ink-secondary font-medium outline-none ml-auto"
          >
            <option value="">All States/UTs</option>
            {statesList.map((s) => (
              <option key={s.state} value={s.state}>
                {s.state}
              </option>
            ))}
          </select>
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-1.5 custom-scrollbar">
          {loading && (
            <div className="py-12 text-center text-xs text-ink-muted">
              Searching Indian meteorological locations...
            </div>
          )}

          {!loading && results.length === 0 && (
            <div className="py-12 text-center text-xs text-ink-muted">
              No matching locations found. Try searching by city or state name.
            </div>
          )}

          {!loading &&
            results.map((loc) => {
              const isSelected = currentLocationId === loc.id;
              const isFav = loc.id ? favorites.includes(loc.id) : false;

              return (
                <div
                  key={loc.id || `${loc.latitude}-${loc.longitude}`}
                  className={`p-3 rounded-xl border flex items-center justify-between gap-3 transition-colors ${
                    isSelected
                      ? "bg-brand-skyLight/50 border-brand-sky"
                      : "bg-white hover:bg-canvas-subtle border-border-subtle"
                  }`}
                >
                  <button
                    onClick={() => {
                      onSelectLocation(loc);
                      onClose();
                    }}
                    className="flex items-center gap-3 flex-1 text-left"
                  >
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                        isSelected
                          ? "bg-brand-sky text-white"
                          : "bg-canvas-subtle text-ink-muted"
                      }`}
                    >
                      {loc.type === "state" ? (
                        <Landmark className="w-4 h-4" />
                      ) : loc.type === "district" ? (
                        <Compass className="w-4 h-4" />
                      ) : (
                        <Building2 className="w-4 h-4" />
                      )}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-ink-primary">
                          {loc.name}
                        </span>
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-ink-muted bg-slate-100 px-1.5 py-0.5 rounded">
                          {loc.type}
                        </span>
                      </div>
                      <p className="text-xs text-ink-secondary mt-0.5">
                        {loc.state} • {loc.latitude.toFixed(2)}°N, {loc.longitude.toFixed(2)}°E
                      </p>
                    </div>
                  </button>

                  <div className="flex items-center gap-2">
                    {loc.id && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onToggleFavorite(loc.id!);
                        }}
                        className={`p-1.5 rounded-lg transition-colors ${
                          isFav
                            ? "text-amber-500 hover:bg-amber-50"
                            : "text-slate-300 hover:text-slate-500 hover:bg-slate-100"
                        }`}
                        title={isFav ? "Remove favorite" : "Bookmark location"}
                      >
                        <Star className={`w-4 h-4 ${isFav ? "fill-current" : ""}`} />
                      </button>
                    )}

                    {isSelected && (
                      <span className="w-6 h-6 rounded-full bg-brand-sky text-white flex items-center justify-center shrink-0">
                        <Check className="w-3.5 h-3.5" />
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
        </div>

        {/* Footer */}
        <div className="p-3 bg-canvas-subtle border-t border-border-subtle text-[11px] text-ink-muted flex items-center justify-between">
          <span>Search across 36 Indian States/UTs & curated districts.</span>
          <span className="hidden sm:inline">Press Esc to close</span>
        </div>
      </div>
    </div>
  );
}
