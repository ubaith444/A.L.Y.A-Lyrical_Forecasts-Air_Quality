"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Header } from "../components/layout/Header";
import { Navigation, ActiveTab } from "../components/layout/Navigation";
import { CurrentHero } from "../components/weather/CurrentHero";
import { HourlyScrubber } from "../components/forecast/HourlyScrubber";
import { DailyForecast } from "../components/forecast/DailyForecast";
import { AQICard } from "../components/airquality/AQICard";
import { ClimateDashboard } from "../components/climate/ClimateDashboard";
import { WeatherMap } from "../components/maps/WeatherMap";
import { LocationModal } from "../components/locations/LocationModal";
import { SettingsModal } from "../components/settings/SettingsModal";
import { SourcesModal } from "../components/sources/SourcesModal";
import { ModelStudio } from "../components/ml/ModelStudio";
import { NaturalLanguageWeatherWidget } from "../components/weather/NaturalLanguageWeatherWidget";
import { EarlyWarningDashboard } from "../components/alerts/EarlyWarningDashboard";
import { LiveLocationMonitor } from "../components/location/LiveLocationMonitor";
import { WeatherStory } from "../components/weather/WeatherStory";
import { BestTimeToOutdoor } from "../components/weather/BestTimeToOutdoor";
import { RainAroundYou } from "../components/weather/RainAroundYou";
import { WeatherMemory } from "../components/weather/WeatherMemory";
import { ShareableWeatherCard } from "../components/weather/ShareableWeatherCard";
import { AQICompanion } from "../components/airquality/AQICompanion";
import { getLivingAtmosphere, WeatherStoryData } from "../lib/intelligence";

import {
  AirQualityResponse,
  LocationData,
  WeatherBundleResponse,
} from "../types";
import {
  fetchAirQuality,
  fetchLocationDetail,
  fetchWeather,
} from "../lib/api";
import {
  loadPreferences,
  savePreferences,
  UserPreferences,
} from "../lib/storage";
import { AlertCircle, RefreshCw, Sparkles, ShieldCheck, Bell, X } from "lucide-react";

export default function HomePage() {
  const [preferences, setPreferences] = useState<UserPreferences>(() =>
    loadPreferences()
  );
  const [activeTab, setActiveTab] = useState<ActiveTab>("dashboard");

  // Selected Location
  const [currentLocation, setCurrentLocation] = useState<LocationData | null>({
    id: "chennai",
    name: "Chennai",
    state: "Tamil Nadu",
    type: "city",
    latitude: 13.0827,
    longitude: 80.2707,
    timezone: "Asia/Kolkata",
    representation: "Municipal city center coordinates (Tamil Nadu)",
  });

  // Weather & AQI independent states
  const [weatherData, setWeatherData] = useState<WeatherBundleResponse | null>(null);
  const [airQualityData, setAirQualityData] = useState<AirQualityResponse | null>(null);

  const [loadingWeather, setLoadingWeather] = useState<boolean>(true);
  const [loadingAQI, setLoadingAQI] = useState<boolean>(true);

  const [weatherError, setWeatherError] = useState<string | null>(null);
  const [aqiError, setAQIError] = useState<string | null>(null);

  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  // Modals
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [isShareCardOpen, setIsShareCardOpen] = useState<boolean>(false);
  const [shareStoryData, setShareStoryData] = useState<WeatherStoryData | null>(null);
  const [isAlertDismissed, setIsAlertDismissed] = useState<boolean>(false);

  // Living Atmosphere state
  const livingAtmosphere = useMemo(() => getLivingAtmosphere(), []);

  // Smart Weather Alert determination
  const smartAlert = useMemo(() => {
    if (!weatherData?.hourly?.items) return null;
    const next12 = weatherData.hourly.items.slice(0, 12);
    const rainItem = next12.find((h: any) => {
      const prob = h.precipitation_probability ?? h.values?.precipitation_probability ?? 0;
      return Number(prob) >= 55;
    });
    const highTemp = weatherData.current?.values?.temperature_2m;
    if (rainItem) {
      const prob = (rainItem as any).precipitation_probability ?? (rainItem as any).values?.precipitation_probability ?? 60;
      const hour = new Date(rainItem.time).getHours();
      const timeStr = `${hour % 12 || 12} ${hour >= 12 ? "PM" : "AM"}`;
      return {
        type: "rain" as const,
        title: "Rain Expected Today",
        description: `Showers anticipated around ${timeStr} (${prob}% probability). Commuters advised to carry rainwear.`,
      };
    }
    if (highTemp && highTemp >= 35) {
      return {
        type: "heat" as const,
        title: "Elevated Heat Advisory",
        description: `High surface temperatures reaching ${highTemp}°C. Stay hydrated and avoid strenuous midday sun exposure.`,
      };
    }
    return null;
  }, [weatherData]);

  // Health check
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch("http://localhost:8000/api/v1/health");
        if (res.ok) {
          setIsBackendHealthy(true);
        } else {
          setIsBackendHealthy(false);
        }
      } catch {
        setIsBackendHealthy(false);
      }
    }
    checkHealth();
  }, []);

  // Fetch location detail if ID changes
  const loadLocation = useCallback(async (locId: string) => {
    try {
      const detail = await fetchLocationDetail(locId);
      setCurrentLocation(detail);
    } catch (err) {
      console.warn("Could not load location detail from API:", err);
    }
  }, []);

  // Sync preferences with storage
  const handleUpdatePreferences = useCallback((updated: Partial<UserPreferences>) => {
    setPreferences((prev) => {
      const next = savePreferences(updated);
      return next;
    });
  }, []);

  // Toggle favorite location
  const handleToggleFavorite = useCallback((locId: string) => {
    setPreferences((prev) => {
      const exists = prev.favoriteLocationIds.includes(locId);
      const nextFavs = exists
        ? prev.favoriteLocationIds.filter((id) => id !== locId)
        : [...prev.favoriteLocationIds, locId];
      return savePreferences({ favoriteLocationIds: nextFavs });
    });
  }, []);

  // Handle location selection
  const handleSelectLocation = useCallback(
    (loc: LocationData) => {
      setCurrentLocation(loc);
      if (loc.id) {
        handleUpdatePreferences({ selectedLocationId: loc.id });
      }
    },
    [handleUpdatePreferences]
  );

  const handleSelectLocationById = useCallback(
    async (locId: string) => {
      await loadLocation(locId);
      handleUpdatePreferences({ selectedLocationId: locId });
    },
    [loadLocation, handleUpdatePreferences]
  );

  // Independent Data Fetching: Weather
  const loadWeatherData = useCallback(
    async (signal?: AbortSignal) => {
      if (!currentLocation) return;
      try {
        setLoadingWeather(true);
        setWeatherError(null);
        const data = await fetchWeather({
          locationId: currentLocation.id,
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude,
          signal,
        });
        setWeatherData(data);
      } catch (err: any) {
        if (
          err.name === "AbortError" ||
          signal?.aborted ||
          err.message?.toLowerCase().includes("abort")
        ) {
          return;
        }
        setWeatherError(err.message || "Failed to load weather forecast");
      } finally {
        if (!signal?.aborted) {
          setLoadingWeather(false);
        }
      }
    },
    [currentLocation]
  );

  // Independent Data Fetching: Air Quality
  const loadAQIData = useCallback(
    async (signal?: AbortSignal) => {
      if (!currentLocation) return;
      try {
        setLoadingAQI(true);
        setAQIError(null);
        const data = await fetchAirQuality({
          locationId: currentLocation.id,
          latitude: currentLocation.latitude,
          longitude: currentLocation.longitude,
          signal,
        });
        setAirQualityData(data);
      } catch (err: any) {
        if (
          err.name === "AbortError" ||
          signal?.aborted ||
          err.message?.toLowerCase().includes("abort")
        ) {
          return;
        }
        setAQIError(err.message || "Failed to load air quality index");
      } finally {
        if (!signal?.aborted) {
          setLoadingAQI(false);
        }
      }
    },
    [currentLocation]
  );

  // Trigger independent data fetches on location change
  useEffect(() => {
    const controller = new AbortController();
    loadWeatherData(controller.signal);
    loadAQIData(controller.signal);

    return () => {
      controller.abort();
    };
  }, [loadWeatherData, loadAQIData]);

  // Dynamic atmospheric gradient class based on hour and conditions
  const atmosphericClass = useMemo(() => {
    const hour = new Date().getHours();
    const isRain =
      weatherData?.current?.values?.precipitation &&
      Number(weatherData.current.values.precipitation) > 0.5;

    if (isRain) return "atmospheric-rain";
    if (hour >= 6 && hour < 11) return "atmospheric-morning";
    if (hour >= 11 && hour < 16) return "atmospheric-day";
    if (hour >= 16 && hour < 19) return "atmospheric-evening";
    return "atmospheric-night";
  }, [weatherData]);

  return (
    <div className={`min-h-screen flex flex-col transition-colors duration-1000 ${atmosphericClass}`}>
      {/* Sticky App Header */}
      <Header
        currentLocation={currentLocation}
        temperatureUnit={preferences.temperatureUnit}
        onToggleUnit={() =>
          handleUpdatePreferences({
            temperatureUnit: preferences.temperatureUnit === "C" ? "F" : "C",
          })
        }
        onOpenSearch={() => setIsSearchOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        isBackendHealthy={isBackendHealthy}
      />

      {/* Navigation Sub-bar */}
      <Navigation activeTab={activeTab} onSelectTab={setActiveTab} />

      {/* Main Dashboard Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 flex flex-col gap-6">
        {/* Isolated Weather Error banner */}
        {weatherError && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>
                <strong>Weather Ingestion Notice:</strong> {weatherError}
              </span>
            </div>
            <button
              onClick={() => loadWeatherData()}
              className="flex items-center gap-1 font-semibold text-amber-800 hover:text-amber-950 underline shrink-0"
            >
              <RefreshCw className="w-3 h-3" />
              Retry
            </button>
          </div>
        )}

        {/* View 1: Main Dashboard Overview with Minimal Dynamic Intelligence */}
        {activeTab === "dashboard" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            {/* Smart Weather Alerts Banner (Dismissible) */}
            {smartAlert && !isAlertDismissed && (
              <div className="bg-amber-50/90 border border-amber-200 rounded-2xl p-4 flex items-center justify-between gap-3 text-xs text-amber-900 shadow-xs animate-in slide-in-from-top-2">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg bg-amber-100 flex items-center justify-center text-amber-700 shrink-0">
                    <Bell className="w-4 h-4 animate-bounce" />
                  </div>
                  <div>
                    <strong className="font-bold text-amber-900">{smartAlert.title}: </strong>
                    <span className="text-amber-800">{smartAlert.description}</span>
                  </div>
                </div>
                <button
                  onClick={() => setIsAlertDismissed(true)}
                  className="p-1 rounded-lg hover:bg-amber-100 text-amber-700 shrink-0 transition-all"
                  title="Dismiss alert"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            {/* Feature 1: Weather Story (Dynamically generated daily summary & 4-phase timeline) */}
            <WeatherStory
              location={currentLocation}
              current={weatherData?.current || null}
              hourlyItems={weatherData?.hourly?.items || []}
              dailyItems={weatherData?.daily?.items || []}
              temperatureUnit={preferences.temperatureUnit}
              savedPlaces={{
                homeId: preferences.homeLocationId,
                workId: preferences.workLocationId,
              }}
              onSelectSavedPlace={handleSelectLocationById}
              onOpenShareCard={(story) => {
                setShareStoryData(story);
                setIsShareCardOpen(true);
              }}
            />

            {/* Feature 2 & 3: The Best Time to Go & Air Quality Companion */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
              <BestTimeToOutdoor
                hourlyItems={weatherData?.hourly?.items || []}
                dailyItems={weatherData?.daily?.items || []}
                aqiData={airQualityData}
              />
              <AQICompanion
                data={airQualityData}
                isLoading={loadingAQI}
              />
            </div>

            {/* Feature 4: Rain Around You (Compact 12-hour precipitation timeline) */}
            <RainAroundYou
              hourlyItems={weatherData?.hourly?.items || []}
            />

            {/* Feature 5: Weather Memory (Yesterday delta, weekly rainfall trend, extremes, Monsoon Watch) */}
            <WeatherMemory
              location={currentLocation}
              current={weatherData?.current || null}
              dailyItems={weatherData?.daily?.items || []}
            />

            {/* Feature 6: Natural-Language Weather Intelligence Query Assistant */}
            <NaturalLanguageWeatherWidget
              location={currentLocation}
              currentTemp={weatherData?.current?.values?.temperature_2m}
              dailyPrecip={weatherData?.current?.values?.precipitation}
            />

            {/* Geographic Station & Topography Map Preview */}
            <div className="mt-1">
              <WeatherMap
                currentLocation={currentLocation}
                onSelectLocation={handleSelectLocation}
              />
            </div>
          </div>
        )}

        {/* View: Live Location Monitor */}
        {activeTab === "live" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            <LiveLocationMonitor />
          </div>
        )}

        {/* View 2: 72h Hourly Scrubber */}
        {activeTab === "hourly" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            <HourlyScrubber
              items={weatherData?.hourly?.items || []}
              temperatureUnit={preferences.temperatureUnit}
              is24Hour={preferences.is24Hour}
            />
            <DailyForecast
              items={weatherData?.daily?.items || []}
              temperatureUnit={preferences.temperatureUnit}
            />
          </div>
        )}

        {/* View 3: 14-Day Extended Outlook */}
        {activeTab === "daily" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            <DailyForecast
              items={weatherData?.daily?.items || []}
              temperatureUnit={preferences.temperatureUnit}
            />
          </div>
        )}

        {/* View 4: Air Quality Deep Dive */}
        {activeTab === "airquality" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            {aqiError && (
              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>
                    <strong>Air Quality Ingestion Notice:</strong> {aqiError}
                  </span>
                </div>
                <button
                  onClick={() => loadAQIData()}
                  className="flex items-center gap-1 font-semibold text-amber-800 hover:underline shrink-0"
                >
                  <RefreshCw className="w-3 h-3" />
                  Retry
                </button>
              </div>
            )}
            <AQICard data={airQualityData} />
          </div>
        )}

        {/* View: Intelligent Early-Warning & Disaster Alert System */}
        {activeTab === "alerts" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            <EarlyWarningDashboard
              currentLocation={currentLocation}
              onSelectLocation={(locId) => {
                handleSelectLocationById(locId);
              }}
            />
          </div>
        )}

        {/* View 5: Climate Intelligence & Heat Patterns */}
        {activeTab === "climate" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            <ClimateDashboard
              locationId={currentLocation?.id || "chennai"}
              temperatureUnit={preferences.temperatureUnit}
            />
          </div>
        )}

        {/* View 6: Weather Map */}
        {activeTab === "map" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            <WeatherMap
              currentLocation={currentLocation}
              onSelectLocation={handleSelectLocation}
            />
          </div>
        )}

        {/* View 7: Unified Model Studio (Consolidated ML Development, Forecasting & Intelligence) */}
        {activeTab === "ml" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            <ModelStudio currentLocation={currentLocation} />
          </div>
        )}

        {/* View 8: Data Sources & Provenance */}
        {activeTab === "sources" && (
          <div className="flex flex-col gap-6 animate-in fade-in duration-300">
            <SourcesModal />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-border-subtle bg-white/70 backdrop-blur-md px-4 py-6 text-center text-xs text-ink-muted flex flex-col sm:flex-row items-center justify-between gap-4 max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-2.5">
          <img
            src="/logo.png"
            alt="A.L.Y.A"
            className="w-5 h-5 object-contain"
          />
          <span className="font-serif font-bold text-ink-primary tracking-wide text-sm">
            A.L.Y.A
          </span>
          <span className="text-ink-secondary">
            — Weather Forecasting, Air Quality &amp; Climate Intelligence
          </span>
        </div>
        <div className="flex items-center gap-3 text-[11px] text-ink-secondary">
          <span>The sky, simplified.</span>
          <span>•</span>
          <span>Light Theme Only</span>
          <span>•</span>
          <span>CPCB NAQI Standard</span>
        </div>
      </footer>

      {/* Search Location Modal */}
      <LocationModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        currentLocationId={currentLocation?.id || null}
        onSelectLocation={handleSelectLocation}
        favorites={preferences.favoriteLocationIds}
        onToggleFavorite={handleToggleFavorite}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        preferences={preferences}
        onUpdatePreferences={handleUpdatePreferences}
        favoriteLocations={preferences.favoriteLocationIds.map((id) => ({
          id,
          name: id.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
          state: id.includes("chennai") || id.includes("coimbatore") || id.includes("nilgiris")
            ? "Tamil Nadu"
            : "India",
        }))}
        onSelectLocationId={(id) => {
          loadLocation(id);
        }}
        onRemoveFavorite={handleToggleFavorite}
      />

      {/* Shareable Weather Card Modal */}
      <ShareableWeatherCard
        isOpen={isShareCardOpen}
        onClose={() => setIsShareCardOpen(false)}
        location={currentLocation}
        current={weatherData?.current || null}
        story={shareStoryData}
      />
    </div>
  );
}
