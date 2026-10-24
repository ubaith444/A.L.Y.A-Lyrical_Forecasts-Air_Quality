import { describe, it, expect, vi } from "vitest";
import {
  fetchLiveMonitorDossier,
  logLocationMovement,
  fetchMovementHistory,
} from "../lib/api";

describe("Live Location Monitor Frontend APIs & Integration", () => {
  it("defines live monitor API methods", () => {
    expect(typeof fetchLiveMonitorDossier).toBe("function");
    expect(typeof logLocationMovement).toBe("function");
    expect(typeof fetchMovementHistory).toBe("function");
  });

  it("fetches live monitor dossier with exact device coordinates and accuracy", async () => {
    const mockDossier = {
      device_location: {
        latitude: 13.0475,
        longitude: 80.2824,
        accuracy_m: 14.5,
        recorded_at: "2026-10-24T12:00:00Z",
        tracking_mode: "Browser Geolocation (High Accuracy)",
      },
      weather: {
        temperature: 31.5,
        apparent_temperature: 37.2,
        relative_humidity: 78,
        precipitation: 0.0,
        wind_speed: 14.2,
      },
      air_quality: {
        aqi: 82,
        category: "Satisfactory",
        prominent_pollutant: "PM2.5",
        pollutants: {
          pm2_5: 28.4,
          pm10: 55.1,
        },
      },
      nearby_microclimates: [
        {
          sector: "N",
          label: "+5 km North Sector",
          distance_km: 5.0,
          latitude: 13.0925,
          longitude: 80.2824,
          estimated_temperature_c: 31.5,
          estimated_humidity_pct: 78.0,
          wind_speed_kmh: 14.2,
          status: "Sampled (+5 km microclimate)",
        },
      ],
      provenance_and_transparency: {
        gps_device: "Device Geolocation API (Reported Accuracy: ±14.5m)",
        weather_grid: "Open-Meteo ECMWF IFS / GFS Model (0.1° grid approximation, ~10 km)",
        air_quality_grid: "Copernicus Atmosphere Monitoring Service (CAMS 0.25° grid)",
        distinction_note: "Device GPS reports live physical coordinates.",
        recommended_refresh_interval_s: 120,
      },
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockDossier,
    });
    global.fetch = mockFetch;

    const res = await fetchLiveMonitorDossier({
      latitude: 13.0475,
      longitude: 80.2824,
      accuracyM: 14.5,
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("/api/v1/live-monitor/dossier");
    expect(url).toContain("latitude=13.0475");
    expect(url).toContain("longitude=80.2824");
    expect(url).toContain("accuracy_m=14.5");

    expect(res.device_location.accuracy_m).toBe(14.5);
    expect(res.weather.temperature).toBe(31.5);
    expect(res.air_quality.aqi).toBe(82);
    expect(res.nearby_microclimates.length).toBeGreaterThan(0);
  });

  it("posts movement logging event when distance threshold is exceeded", async () => {
    const mockMovementResponse = {
      event_id: "mov-uuid-5678",
      distance_moved_m: 620.5,
      trigger_exceeded: true,
      threshold_m: 500.0,
      timestamp: "2026-10-24T12:05:00Z",
    };

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockMovementResponse,
    });
    global.fetch = mockFetch;

    const res = await logLocationMovement({
      latitude: 13.052,
      longitude: 80.285,
      accuracyM: 12.0,
      previousLat: 13.0475,
      previousLon: 80.2824,
      thresholdM: 500,
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const call = mockFetch.mock.calls[0];
    expect(call[0]).toContain("/api/v1/live-monitor/log-movement");
    expect(call[1].method).toBe("POST");
    const body = JSON.parse(call[1].body);
    expect(body.threshold_m).toBe(500);
    expect(body.latitude).toBe(13.052);
    expect(res.trigger_exceeded).toBe(true);
    expect(res.distance_moved_m).toBeGreaterThan(500);
  });
});
