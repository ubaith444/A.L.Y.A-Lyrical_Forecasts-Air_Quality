"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import {
  Navigation,
  Navigation2,
  MapPin,
  RefreshCw,
  Compass,
  Wind,
  Droplets,
  Thermometer,
  ShieldAlert,
  ShieldCheck,
  Pause,
  Play,
  RotateCcw,
  Sliders,
  CheckCircle2,
  AlertTriangle,
  Info,
  Clock,
  Radio,
  Eye,
  EyeOff,
  CloudRain,
  Gauge,
  Layers,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import {
  fetchLiveMonitorDossier,
  logLocationMovement,
  fetchMovementHistory,
  LiveMonitorDossier,
} from "../../lib/api";

// Dynamically import Leaflet interactive map with ssr: false to prevent hydration crash
const LiveLeafletMap = dynamic(
  () => import("./LiveLeafletMap"),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[400px] sm:h-[480px] rounded-2xl bg-canvas-subtle border border-border-subtle flex flex-col items-center justify-center gap-3 animate-pulse">
        <MapPin className="w-8 h-8 text-brand-sky animate-bounce" />
        <span className="text-xs font-medium text-ink-secondary">
          Initializing Interactive Leaflet Map & GPS Canvas...
        </span>
      </div>
    ),
  }
);

// Pre-configured simulated field locations for instant testing / demonstration
const SIMULATION_LOCATIONS = [
  {
    name: "Marina Beach, Chennai",
    state: "Tamil Nadu",
    lat: 13.0475,
    lon: 80.2824,
    desc: "Coastal high-humidity shoreline zone",
  },
  {
    name: "Nilgiris (Ooty High Plateau)",
    state: "Tamil Nadu",
    lat: 11.4102,
    lon: 76.695,
    desc: "High-altitude montane microclimate (~2240m)",
  },
  {
    name: "Coimbatore Peelamedu",
    state: "Tamil Nadu",
    lat: 11.0267,
    lon: 77.0177,
    desc: "Inland rainshadow plateau & industrial belt",
  },
  {
    name: "Madurai Meenakshi Basin",
    state: "Tamil Nadu",
    lat: 9.9195,
    lon: 78.1193,
    desc: "Southern semi-arid river valley plain",
  },
  {
    name: "Kanyakumari Cape",
    state: "Tamil Nadu",
    lat: 8.0883,
    lon: 77.5385,
    desc: "Peninsular tri-sea oceanic convergence",
  },
];

// Client-side Haversine calculation in meters
function computeHaversineMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371000; // Earth radius in meters
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

// Map AQI category to Alya pastel color schemes
function getAQIBadge(category?: string) {
  switch (category?.toLowerCase()) {
    case "good":
      return {
        bg: "bg-emerald-50 text-emerald-800 border-emerald-200",
        pill: "bg-emerald-500",
        label: "Good (Minimal Impact)",
      };
    case "satisfactory":
      return {
        bg: "bg-teal-50 text-teal-800 border-teal-200",
        pill: "bg-teal-500",
        label: "Satisfactory (Minor Breathing Discomfort)",
      };
    case "moderate":
      return {
        bg: "bg-amber-50 text-amber-800 border-amber-200",
        pill: "bg-amber-500",
        label: "Moderate (Breathing Discomfort for Sensitive)",
      };
    case "poor":
      return {
        bg: "bg-orange-50 text-orange-800 border-orange-200",
        pill: "bg-orange-500",
        label: "Poor (Breathing Discomfort to Most People)",
      };
    case "very poor":
      return {
        bg: "bg-rose-50 text-rose-800 border-rose-200",
        pill: "bg-rose-500",
        label: "Very Poor (Respiratory Illness on Prolonged Exposure)",
      };
    case "severe":
      return {
        bg: "bg-red-50 text-red-900 border-red-300",
        pill: "bg-red-700",
        label: "Severe (Affects Healthy People Severely)",
      };
    default:
      return {
        bg: "bg-slate-50 text-slate-700 border-slate-200",
        pill: "bg-slate-400",
        label: "Analyzing Data...",
      };
  }
}

export function LiveLocationMonitor() {
  // Device Geolocation state
  const [coords, setCoords] = useState<{
    latitude: number;
    longitude: number;
    accuracy_m: number;
  } | null>(null);
  const [previousCoords, setPreviousCoords] = useState<{
    latitude: number;
    longitude: number;
  } | null>(null);

  const [trackingStatus, setTrackingStatus] = useState<
    "idle" | "requesting" | "active" | "paused" | "denied" | "unsupported" | "simulated"
  >("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [highAccuracy, setHighAccuracy] = useState<boolean>(true);

  // Data dossier state
  const [dossier, setDossier] = useState<LiveMonitorDossier | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);

  // Settings & Configuration
  const [refreshIntervalSec, setRefreshIntervalSec] = useState<number>(120); // 2 minutes default
  const [secondsRemaining, setSecondsRemaining] = useState<number>(120);
  const [movementThresholdM, setMovementThresholdM] = useState<number>(500); // 500m default
  const [distanceMovedM, setDistanceMovedM] = useState<number>(0);
  const [movementTriggered, setMovementTriggered] = useState<boolean>(false);

  // Audit history
  const [movementLogs, setMovementLogs] = useState<any[]>([]);

  // Refs for tracking and timers
  const watchIdRef = useRef<number | null>(null);
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 1. Fetch live dossier from backend API
  const loadDossier = useCallback(
    async (lat: number, lon: number, accuracyM?: number) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      setIsLoading(true);
      setErrorMessage(null);

      try {
        const data = await fetchLiveMonitorDossier({
          latitude: lat,
          longitude: lon,
          accuracyM,
          signal: abortControllerRef.current.signal,
        });
        setDossier(data);
        setLastRefreshedAt(new Date());
        setSecondsRemaining(refreshIntervalSec);
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error("Failed to load live monitor dossier:", err);
          setErrorMessage(err.message || "Failed to load live weather/AQI for current coordinates.");
        }
      } finally {
        setIsLoading(false);
      }
    },
    [refreshIntervalSec]
  );

  // 2. Evaluate location update and movement
  const handleLocationUpdate = useCallback(
    async (lat: number, lon: number, accuracyM: number) => {
      setCoords({ latitude: lat, longitude: lon, accuracy_m: accuracyM });

      if (previousCoords) {
        const dist = computeHaversineMeters(
          previousCoords.latitude,
          previousCoords.longitude,
          lat,
          lon
        );
        setDistanceMovedM(dist);

        if (dist >= movementThresholdM) {
          setMovementTriggered(true);
          // Log movement event to backend
          try {
            await logLocationMovement({
              latitude: lat,
              longitude: lon,
              accuracyM,
              previousLat: previousCoords.latitude,
              previousLon: previousCoords.longitude,
              thresholdM: movementThresholdM,
            });
            // Refresh movement history
            const hist = await fetchMovementHistory(10);
            setMovementLogs(hist.items || []);
          } catch (e) {
            console.warn("Could not log movement event:", e);
          }
          // Update baseline coordinates and re-fetch dossier
          setPreviousCoords({ latitude: lat, longitude: lon });
          loadDossier(lat, lon, accuracyM);
          return;
        }
      } else {
        setPreviousCoords({ latitude: lat, longitude: lon });
        loadDossier(lat, lon, accuracyM);
      }
    },
    [previousCoords, movementThresholdM, loadDossier]
  );

  // 3. Start Browser Geolocation Tracking
  const startLiveTracking = useCallback(() => {
    if (!navigator.geolocation) {
      setTrackingStatus("unsupported");
      setErrorMessage("Geolocation is not supported by your browser environment.");
      return;
    }

    setTrackingStatus("requesting");
    setErrorMessage(null);

    // Initial immediate fix
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setTrackingStatus("active");
        handleLocationUpdate(
          pos.coords.latitude,
          pos.coords.longitude,
          pos.coords.accuracy
        );

        // Clear existing watch if any
        if (watchIdRef.current !== null) {
          navigator.geolocation.clearWatch(watchIdRef.current);
        }

        // Setup continuous watchPosition
        watchIdRef.current = navigator.geolocation.watchPosition(
          (watchPos) => {
            handleLocationUpdate(
              watchPos.coords.latitude,
              watchPos.coords.longitude,
              watchPos.coords.accuracy
            );
          },
          (err) => {
            console.warn("watchPosition warning:", err);
          },
          {
            enableHighAccuracy: highAccuracy,
            timeout: 20000,
            maximumAge: 10000,
          }
        );
      },
      (err) => {
        console.warn("getCurrentPosition error:", err);
        if (err.code === err.PERMISSION_DENIED) {
          setTrackingStatus("denied");
          setErrorMessage(
            "GPS location access was denied. You can select one of the simulated field locations below or enable location permissions in browser settings."
          );
        } else {
          setTrackingStatus("denied");
          setErrorMessage(
            `Unable to acquire GPS fix: ${err.message}. You can test with a simulated coordinate.`
          );
        }
      },
      {
        enableHighAccuracy: highAccuracy,
        timeout: 15000,
      }
    );
  }, [highAccuracy, handleLocationUpdate]);

  // 4. Pause Tracking
  const pauseTracking = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setTrackingStatus("paused");
  };

  // 5. Resume Tracking
  const resumeTracking = () => {
    startLiveTracking();
  };

  // 6. Stop / Revoke Tracking
  const revokeTracking = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setCoords(null);
    setPreviousCoords(null);
    setDossier(null);
    setTrackingStatus("idle");
    setDistanceMovedM(0);
    setMovementTriggered(false);
  };

  // 7. Test using a simulated location
  const selectSimulatedLocation = (loc: (typeof SIMULATION_LOCATIONS)[0]) => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setTrackingStatus("simulated");
    setErrorMessage(null);
    const simulatedAccuracy = 12.0; // 12 meters
    setCoords({ latitude: loc.lat, longitude: loc.lon, accuracy_m: simulatedAccuracy });
    setPreviousCoords({ latitude: loc.lat, longitude: loc.lon });
    loadDossier(loc.lat, loc.lon, simulatedAccuracy);
  };

  // 8. Countdown Timer for Periodic Weather Refresh
  useEffect(() => {
    if (countdownIntervalRef.current) {
      clearInterval(countdownIntervalRef.current);
    }

    if (
      (trackingStatus === "active" || trackingStatus === "simulated") &&
      refreshIntervalSec > 0 &&
      coords
    ) {
      countdownIntervalRef.current = setInterval(() => {
        setSecondsRemaining((prev) => {
          if (prev <= 1) {
            // Trigger automatic refresh
            loadDossier(coords.latitude, coords.longitude, coords.accuracy_m);
            return refreshIntervalSec;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }
    };
  }, [trackingStatus, refreshIntervalSec, coords, loadDossier]);

  // Initial fetch of recent movement logs
  useEffect(() => {
    fetchMovementHistory(10)
      .then((res) => setMovementLogs(res.items || []))
      .catch(() => {});
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const aqiBadge = getAQIBadge(dossier?.air_quality?.category);

  return (
    <div className="flex flex-col gap-6">
      {/* Header Banner: Feature Identity & Live GPS Status */}
      <div className="bg-white rounded-2xl p-5 border border-border-subtle shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-brand-aquaLight flex items-center justify-center text-brand-deepTeal">
              <Radio className="w-4 h-4 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base font-bold text-ink-primary flex items-center gap-2">
                <span>Live Location Monitor & Surrounding Atmosphere</span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-brand-skyLight text-brand-sky border border-brand-sky/20">
                  Microclimate Radar
                </span>
              </h2>
              <p className="text-xs text-ink-secondary">
                Continuous device GPS positioning paired with real-time weather and official CPCB AQI observations.
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls & GPS State Pill */}
        <div className="flex items-center flex-wrap gap-2">
          {trackingStatus === "active" && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
              <span>GPS Tracking Active (±{Math.round(coords?.accuracy_m || 15)}m)</span>
            </div>
          )}

          {trackingStatus === "simulated" && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-sky-50 border border-sky-200 text-sky-800 text-xs font-semibold">
              <Compass className="w-3.5 h-3.5 text-brand-sky" />
              <span>Simulated Field Coordinates</span>
            </div>
          )}

          {trackingStatus === "paused" && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
              <Pause className="w-3 h-3 text-amber-600" />
              <span>Tracking Paused</span>
            </div>
          )}

          {/* Primary Action Buttons */}
          {trackingStatus === "idle" || trackingStatus === "denied" || trackingStatus === "unsupported" ? (
            <button
              onClick={startLiveTracking}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-sky hover:bg-brand-sky/90 text-white text-xs font-bold shadow-sm transition-all"
            >
              <Navigation className="w-3.5 h-3.5" />
              <span>Enable Device GPS</span>
            </button>
          ) : (
            <div className="flex items-center gap-1.5">
              {trackingStatus === "active" ? (
                <button
                  onClick={pauseTracking}
                  title="Temporarily halt background GPS polling"
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border-subtle bg-white hover:bg-canvas-subtle text-ink-secondary text-xs font-medium transition-all"
                >
                  <Pause className="w-3.5 h-3.5" />
                  <span>Pause</span>
                </button>
              ) : (
                <button
                  onClick={resumeTracking}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-medium transition-all"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Resume</span>
                </button>
              )}

              <button
                onClick={() => {
                  if (coords) loadDossier(coords.latitude, coords.longitude, coords.accuracy_m);
                }}
                disabled={isLoading}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border-subtle bg-white hover:bg-canvas-subtle text-ink-secondary text-xs font-medium transition-all"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-brand-sky" : ""}`} />
                <span>Refresh</span>
              </button>

              <button
                onClick={revokeTracking}
                title="Revoke and clear location coordinates"
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-rose-200 bg-rose-50/50 hover:bg-rose-100/50 text-rose-700 text-xs font-medium transition-all"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Stop</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Movement Triggered Toast Banner */}
      {movementTriggered && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-emerald-900 animate-in fade-in slide-in-from-top-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Movement Detected:</strong> Device shifted by{" "}
              <strong>{distanceMovedM} meters</strong> (exceeded {movementThresholdM}m threshold). Atmospheric weather and AQI have automatically refreshed for your new surroundings.
            </span>
          </div>
          <button
            onClick={() => setMovementTriggered(false)}
            className="text-xs text-emerald-700 hover:underline font-semibold ml-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Error / Permission Denied Callout */}
      {errorMessage && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex flex-col gap-2 text-xs text-amber-900">
          <div className="flex items-center gap-2 font-bold text-amber-800">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Location Sensor Notice</span>
          </div>
          <p className="text-amber-800/90">{errorMessage}</p>
        </div>
      )}

      {/* Quick-Select Simulated Coordinates Chips (Crucial for Instant Verification without moving) */}
      <div className="bg-white rounded-2xl p-4 border border-border-subtle shadow-sm flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-bold text-ink-primary">
            <Compass className="w-3.5 h-3.5 text-brand-sky" />
            <span>Field Simulation & Quick Testing Coordinates:</span>
          </div>
          <span className="text-[11px] text-ink-muted">Click any location to simulate live positioning</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {SIMULATION_LOCATIONS.map((loc) => {
            const isSelected =
              coords &&
              Math.abs(coords.latitude - loc.lat) < 0.001 &&
              Math.abs(coords.longitude - loc.lon) < 0.001;
            return (
              <button
                key={loc.name}
                onClick={() => selectSimulatedLocation(loc)}
                className={`px-3 py-1.5 rounded-xl text-xs transition-all flex items-center gap-1.5 ${
                  isSelected
                    ? "bg-brand-deepTeal text-white font-semibold shadow-sm"
                    : "bg-canvas-subtle hover:bg-canvas-subtle/80 border border-border-subtle text-ink-secondary"
                }`}
              >
                <MapPin className={`w-3 h-3 ${isSelected ? "text-white" : "text-brand-sky"}`} />
                <span>{loc.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Monitoring Section: Interactive Leaflet Map & Live Weather Dossier */}
      {coords && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Interactive Leaflet Map (Left Column - 7 Cols) */}
          <div className="lg:col-span-7 flex flex-col gap-4">
            <div className="bg-white rounded-2xl p-4 border border-border-subtle shadow-sm flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Navigation2 className="w-4 h-4 text-brand-sky" />
                  <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
                    Interactive Geospatial Marker & Surroundings
                  </h3>
                </div>
                <div className="flex items-center gap-1 text-[11px] text-ink-muted">
                  <span>GPS Accuracy:</span>
                  <strong className="text-ink-primary font-mono">
                    ±{Math.round(coords.accuracy_m)}m
                  </strong>
                </div>
              </div>

              {/* Leaflet + OpenStreetMap */}
              <LiveLeafletMap
                latitude={coords.latitude}
                longitude={coords.longitude}
                accuracyM={coords.accuracy_m}
                nearbySectors={dossier?.nearby_microclimates || []}
                temperature={dossier?.weather?.temperature}
                apparentTemperature={dossier?.weather?.apparent_temperature}
                humidity={dossier?.weather?.relative_humidity}
              />

              {/* Map Footer: Coordinates & Freshness */}
              <div className="flex items-center justify-between text-[11px] text-ink-muted pt-1 px-1">
                <div className="flex items-center gap-2">
                  <span>Lat: <strong className="font-mono text-ink-secondary">{coords.latitude.toFixed(5)}°</strong></span>
                  <span>Lon: <strong className="font-mono text-ink-secondary">{coords.longitude.toFixed(5)}°</strong></span>
                </div>
                {lastRefreshedAt && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>Last synced: {lastRefreshedAt.toLocaleTimeString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Nearby Weather Microclimates Grid (+5 km Sectors) */}
            <div className="bg-white rounded-2xl p-4 border border-border-subtle shadow-sm flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Compass className="w-4 h-4 text-brand-deepTeal" />
                  <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
                    Nearby Weather Microclimate Gradients (+5 km)
                  </h3>
                </div>
                <span className="text-[11px] text-ink-muted">Cardinal Sector Sampling</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {(dossier?.nearby_microclimates || [])
                  .filter((sec: any) => sec.distance_km > 0)
                  .map((sec: any) => {
                    const sectorLabel = sec.sector || sec.direction || "Sector";
                    return (
                      <div
                        key={`${sec.latitude}-${sec.longitude}`}
                        className="p-3 rounded-xl bg-canvas-subtle border border-border-subtle flex flex-col gap-1.5 transition-all hover:border-brand-sky/40"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-white text-brand-deepTeal border border-border-subtle">
                            {sectorLabel}
                          </span>
                          <span className="text-[10px] text-ink-muted font-mono">{sec.distance_km}km</span>
                        </div>
                        <div className="text-sm font-bold text-ink-primary font-mono">
                          {sec.estimated_temperature_c}°C
                        </div>
                        <div className="flex items-center justify-between text-[10px] text-ink-secondary">
                          <span>RH: {sec.estimated_humidity_pct}%</span>
                          <span>{sec.wind_speed_kmh} km/h</span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          {/* Real-Time Weather & Live AQI (Right Column - 5 Cols) */}
          <div className="lg:col-span-5 flex flex-col gap-4">
            {/* Current Weather Card */}
            <div className="bg-white rounded-2xl p-5 border border-border-subtle shadow-sm flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-brand-skyLight flex items-center justify-center text-brand-sky">
                    <Thermometer className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
                      Immediate Weather
                    </h3>
                    <span className="text-[11px] text-ink-muted">Ground-level surface readings</span>
                  </div>
                </div>

                {/* Auto Refresh Countdown Badge */}
                <div className="flex items-center gap-1.5 text-[11px] font-mono text-ink-secondary bg-canvas-subtle px-2.5 py-1 rounded-lg border border-border-subtle">
                  <Clock className="w-3 h-3 text-brand-sky" />
                  <span>Next: {secondsRemaining}s</span>
                </div>
              </div>

              {/* Main Temperature Display */}
              <div className="flex items-baseline justify-between">
                <div>
                  <div className="text-4xl font-extrabold text-ink-primary font-mono tracking-tight">
                    {dossier?.weather?.temperature !== undefined
                      ? `${dossier.weather.temperature}°C`
                      : "—"}
                  </div>
                  <div className="text-xs text-ink-secondary mt-0.5">
                    Feels like{" "}
                    <strong className="text-ink-primary">
                      {dossier?.weather?.apparent_temperature !== undefined
                        ? `${dossier.weather.apparent_temperature}°C`
                        : "—"}
                    </strong>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs font-semibold text-brand-deepTeal">
                    {dossier?.weather?.cloud_cover !== undefined
                      ? `${dossier.weather.cloud_cover}% Cloud Cover`
                      : "Partly Cloudy"}
                  </div>
                  <div className="text-[11px] text-ink-muted">
                    Precip: {dossier?.weather?.precipitation ?? 0} mm
                  </div>
                </div>
              </div>

              {/* Weather Metrics Grid */}
              <div className="grid grid-cols-2 gap-2.5 pt-1">
                <div className="p-2.5 rounded-xl bg-canvas-subtle border border-border-subtle flex items-center gap-2.5">
                  <Droplets className="w-4 h-4 text-brand-sky shrink-0" />
                  <div>
                    <div className="text-[10px] text-ink-muted uppercase">Relative Humidity</div>
                    <div className="text-xs font-bold text-ink-primary font-mono">
                      {dossier?.weather?.relative_humidity !== undefined
                        ? `${dossier.weather.relative_humidity}%`
                        : "—"}
                    </div>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-canvas-subtle border border-border-subtle flex items-center gap-2.5">
                  <Wind className="w-4 h-4 text-brand-deepTeal shrink-0" />
                  <div>
                    <div className="text-[10px] text-ink-muted uppercase">Wind Speed & Dir</div>
                    <div className="text-xs font-bold text-ink-primary font-mono">
                      {dossier?.weather?.wind_speed !== undefined
                        ? `${dossier.weather.wind_speed} km/h`
                        : "—"}
                    </div>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-canvas-subtle border border-border-subtle flex items-center gap-2.5">
                  <Gauge className="w-4 h-4 text-brand-mist shrink-0" />
                  <div>
                    <div className="text-[10px] text-ink-muted uppercase">Surface Pressure</div>
                    <div className="text-xs font-bold text-ink-primary font-mono">
                      {dossier?.weather?.surface_pressure != null
                        ? `${dossier.weather.surface_pressure} hPa`
                        : "1012 hPa"}
                    </div>
                  </div>
                </div>

                <div className="p-2.5 rounded-xl bg-canvas-subtle border border-border-subtle flex items-center gap-2.5">
                  <CloudRain className="w-4 h-4 text-brand-sky shrink-0" />
                  <div>
                    <div className="text-[10px] text-ink-muted uppercase">Precipitation</div>
                    <div className="text-xs font-bold text-ink-primary font-mono">
                      {dossier?.weather?.precipitation !== undefined
                        ? `${dossier.weather.precipitation} mm`
                        : "0.0 mm"}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Live AQI Monitoring Card (CPCB / NAQI Standard) */}
            <div className="bg-white rounded-2xl p-5 border border-border-subtle shadow-sm flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-border-subtle pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-teal-50 flex items-center justify-center text-teal-700">
                    <Wind className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
                      Live Air Quality (NAQI)
                    </h3>
                    <span className="text-[11px] text-ink-muted">CPCB Standard Assessment</span>
                  </div>
                </div>

                <div className={`px-2.5 py-1 rounded-full text-[11px] font-bold border flex items-center gap-1.5 ${aqiBadge.bg}`}>
                  <span className={`w-2 h-2 rounded-full ${aqiBadge.pill}`}></span>
                  <span>{dossier?.air_quality?.category || "Calculating"}</span>
                </div>
              </div>

              {/* AQI Score & Prominent Pollutant */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-3xl font-extrabold text-ink-primary font-mono">
                    {dossier?.air_quality?.aqi ?? "—"}
                  </div>
                  <div className="text-xs text-ink-secondary mt-0.5">
                    Prominent: <strong className="text-ink-primary">{dossier?.air_quality?.prominent_pollutant || "PM2.5"}</strong>
                  </div>
                </div>

                <div className="text-right text-xs text-ink-secondary max-w-[180px]">
                  <span>{aqiBadge.label}</span>
                </div>
              </div>

              {/* Pollutants Breakdown */}
              <div className="grid grid-cols-3 gap-2">
                <div className="p-2 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
                  <div className="text-[10px] text-ink-muted">PM2.5</div>
                  <div className="text-xs font-bold text-ink-primary font-mono">
                    {dossier?.air_quality?.pollutants?.pm2_5 !== undefined && dossier.air_quality.pollutants.pm2_5 !== null
                      ? `${dossier.air_quality.pollutants.pm2_5} µg/m³`
                      : "—"}
                  </div>
                </div>

                <div className="p-2 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
                  <div className="text-[10px] text-ink-muted">PM10</div>
                  <div className="text-xs font-bold text-ink-primary font-mono">
                    {dossier?.air_quality?.pollutants?.pm10 !== undefined && dossier.air_quality.pollutants.pm10 !== null
                      ? `${dossier.air_quality.pollutants.pm10} µg/m³`
                      : "—"}
                  </div>
                </div>

                <div className="p-2 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
                  <div className="text-[10px] text-ink-muted">NO₂</div>
                  <div className="text-xs font-bold text-ink-primary font-mono">
                    {dossier?.air_quality?.pollutants?.nitrogen_dioxide !== undefined && dossier.air_quality.pollutants.nitrogen_dioxide !== null
                      ? `${dossier.air_quality.pollutants.nitrogen_dioxide} µg/m³`
                      : "—"}
                  </div>
                </div>

                <div className="p-2 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
                  <div className="text-[10px] text-ink-muted">SO₂</div>
                  <div className="text-xs font-bold text-ink-primary font-mono">
                    {dossier?.air_quality?.pollutants?.sulphur_dioxide !== undefined && dossier.air_quality.pollutants.sulphur_dioxide !== null
                      ? `${dossier.air_quality.pollutants.sulphur_dioxide} µg/m³`
                      : "—"}
                  </div>
                </div>

                <div className="p-2 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
                  <div className="text-[10px] text-ink-muted">O₃</div>
                  <div className="text-xs font-bold text-ink-primary font-mono">
                    {dossier?.air_quality?.pollutants?.ozone !== undefined && dossier.air_quality.pollutants.ozone !== null
                      ? `${dossier.air_quality.pollutants.ozone} µg/m³`
                      : "—"}
                  </div>
                </div>

                <div className="p-2 rounded-xl bg-canvas-subtle border border-border-subtle text-center">
                  <div className="text-[10px] text-ink-muted">CO</div>
                  <div className="text-xs font-bold text-ink-primary font-mono">
                    {dossier?.air_quality?.pollutants?.carbon_monoxide !== undefined && dossier.air_quality.pollutants.carbon_monoxide !== null
                      ? `${dossier.air_quality.pollutants.carbon_monoxide} µg/m³`
                      : "—"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Location Status & Transparency Disclosure Card (Required Specification) */}
      <div className="bg-white rounded-2xl p-5 border border-border-subtle shadow-sm flex flex-col gap-3">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-brand-sky" />
          <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
            Location Status & Meteorological Data Transparency
          </h3>
        </div>

        <p className="text-xs text-ink-secondary leading-relaxed">
          {dossier?.provenance_and_transparency?.distinction_note ||
            "Device GPS provides exact physical coordinates (±18m). However, numerical weather prediction (NWP) models and Copernicus Atmosphere Monitoring Service (CAMS) compute atmospheric variables over grid cells (~10km to 25km resolution). Weather and AQI are simulated and verified for the cell encompassing your position, rather than physical on-site sensor probes at this exact meter."}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          <div className="p-3 rounded-xl bg-canvas-subtle border border-border-subtle text-xs space-y-1">
            <span className="text-[10px] uppercase font-bold text-ink-muted">GPS Device Sensor</span>
            <div className="font-semibold text-ink-primary">
              {dossier?.provenance_and_transparency?.gps_device || `Browser Geolocation API (±${Math.round(coords?.accuracy_m || 18)}m)`}
            </div>
            <div className="text-[11px] text-ink-secondary">High-accuracy satellite / cellular fix</div>
          </div>

          <div className="p-3 rounded-xl bg-canvas-subtle border border-border-subtle text-xs space-y-1">
            <span className="text-[10px] uppercase font-bold text-ink-muted">Weather Model Grid</span>
            <div className="font-semibold text-ink-primary">
              {dossier?.provenance_and_transparency?.weather_grid || "Open-Meteo ECMWF IFS / GFS Model (0.1° grid, ~10 km)"}
            </div>
            <div className="text-[11px] text-ink-secondary">Hourly calibrated reanalysis grid</div>
          </div>

          <div className="p-3 rounded-xl bg-canvas-subtle border border-border-subtle text-xs space-y-1">
            <span className="text-[10px] uppercase font-bold text-ink-muted">Air Quality Model Grid</span>
            <div className="font-semibold text-ink-primary">
              {dossier?.provenance_and_transparency?.air_quality_grid || "Copernicus CAMS 0.25° European Ensemble"}
            </div>
            <div className="text-[11px] text-ink-secondary">CPCB NAQI breakpoint converted</div>
          </div>
        </div>
      </div>

      {/* Privacy Controls & Configurable Refresh Settings */}
      <div className="bg-white rounded-2xl p-5 border border-border-subtle shadow-sm flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-deepTeal" />
            <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
              Privacy Controls & Refresh Configuration
            </h3>
          </div>
          <span className="text-xs text-ink-muted">User Preferences</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          {/* Refresh Interval Selector */}
          <div className="space-y-1.5">
            <label className="font-semibold text-ink-primary block">
              Auto-Refresh Cadence
            </label>
            <select
              value={refreshIntervalSec}
              onChange={(e) => {
                const val = Number(e.target.value);
                setRefreshIntervalSec(val);
                setSecondsRemaining(val);
              }}
              className="w-full bg-canvas-subtle border border-border-subtle rounded-xl px-3 py-2 text-xs text-ink-primary focus:outline-none focus:border-brand-sky"
            >
              <option value={60}>Every 1 minute</option>
              <option value={120}>Every 2 minutes (Recommended)</option>
              <option value={300}>Every 5 minutes</option>
              <option value={900}>Every 15 minutes</option>
              <option value={0}>Manual refresh only</option>
            </select>
          </div>

          {/* Movement Distance Threshold */}
          <div className="space-y-1.5">
            <label className="font-semibold text-ink-primary block">
              Movement Threshold Trigger
            </label>
            <select
              value={movementThresholdM}
              onChange={(e) => setMovementThresholdM(Number(e.target.value))}
              className="w-full bg-canvas-subtle border border-border-subtle rounded-xl px-3 py-2 text-xs text-ink-primary focus:outline-none focus:border-brand-sky"
            >
              <option value={200}>200 meters (Walking sensitive)</option>
              <option value={500}>500 meters (Default standard)</option>
              <option value={1000}>1,000 meters (1 km)</option>
              <option value={2000}>2,000 meters (Commute)</option>
            </select>
          </div>

          {/* High Accuracy Toggle */}
          <div className="space-y-1.5">
            <label className="font-semibold text-ink-primary block">
              High-Accuracy Hardware GPS
            </label>
            <button
              onClick={() => {
                const next = !highAccuracy;
                setHighAccuracy(next);
                if (trackingStatus === "active") {
                  pauseTracking();
                  setTimeout(() => resumeTracking(), 100);
                }
              }}
              className={`w-full px-3 py-2 rounded-xl border flex items-center justify-between text-xs font-semibold transition-all ${
                highAccuracy
                  ? "bg-brand-skyLight border-brand-sky/30 text-brand-sky"
                  : "bg-canvas-subtle border-border-subtle text-ink-secondary"
              }`}
            >
              <span>{highAccuracy ? "Enabled (GPS + Wi-Fi)" : "Standard (Power Saver)"}</span>
              <CheckCircle2 className={`w-3.5 h-3.5 ${highAccuracy ? "opacity-100" : "opacity-0"}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Movement Audit History (Persisted in SQLite / Backend) */}
      {movementLogs.length > 0 && (
        <div className="bg-white rounded-2xl p-5 border border-border-subtle shadow-sm flex flex-col gap-3">
          <div className="flex items-center justify-between border-b border-border-subtle pb-2.5">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-brand-sky" />
              <h3 className="text-xs font-bold text-ink-primary uppercase tracking-wider">
                Session Movement Audit History
              </h3>
            </div>
            <span className="text-[11px] text-ink-muted">{movementLogs.length} logged events</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-border-subtle text-ink-muted">
                  <th className="py-2 px-3 font-semibold">Timestamp</th>
                  <th className="py-2 px-3 font-semibold">Current Coords</th>
                  <th className="py-2 px-3 font-semibold">Distance Moved</th>
                  <th className="py-2 px-3 font-semibold">Accuracy</th>
                  <th className="py-2 px-3 font-semibold">Trigger Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle text-ink-secondary">
                {movementLogs.map((log, idx) => (
                  <tr key={idx} className="hover:bg-canvas-subtle/50">
                    <td className="py-2 px-3 font-mono text-[11px]">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="py-2 px-3 font-mono">
                      {log.latitude?.toFixed(4)}°, {log.longitude?.toFixed(4)}°
                    </td>
                    <td className="py-2 px-3 font-bold text-ink-primary">
                      {Math.round(log.distance_moved_m)} m
                    </td>
                    <td className="py-2 px-3 font-mono text-[11px]">
                      ±{Math.round(log.accuracy_m || 15)}m
                    </td>
                    <td className="py-2 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {log.trigger_exceeded ? "Threshold Exceeded" : "Logged"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
export default LiveLocationMonitor;
