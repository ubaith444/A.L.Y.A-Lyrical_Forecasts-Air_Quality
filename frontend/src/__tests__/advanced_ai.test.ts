import { describe, it, expect, vi } from "vitest";
import {
  fetchPIMLComparison,
  fetchDownscaling,
  fetchMultimodalAssimilation,
  fetchAutoregressiveCorrection,
  fetchCoupledEarthSystem,
  fetchProbabilisticForecast,
  queryNaturalLanguageWeather,
  fetchDataSourcesMatrix,
  fetchRegionalMultimodal,
  fetchAirQualityIntelligence,
  fetchHorizonStrategy,
  fetchModelEvaluationAndDrift,
  fetchArchitectureLayers,
} from "../lib/api";

describe("Advanced AI/ML Feature Architecture API Client", () => {
  it("defines all advanced ML API client methods", () => {
    expect(typeof fetchPIMLComparison).toBe("function");
    expect(typeof fetchDownscaling).toBe("function");
    expect(typeof fetchMultimodalAssimilation).toBe("function");
    expect(typeof fetchAutoregressiveCorrection).toBe("function");
    expect(typeof fetchCoupledEarthSystem).toBe("function");
    expect(typeof fetchProbabilisticForecast).toBe("function");
    expect(typeof queryNaturalLanguageWeather).toBe("function");
    expect(typeof fetchDataSourcesMatrix).toBe("function");
    expect(typeof fetchRegionalMultimodal).toBe("function");
    expect(typeof fetchAirQualityIntelligence).toBe("function");
    expect(typeof fetchHorizonStrategy).toBe("function");
    expect(typeof fetchModelEvaluationAndDrift).toBe("function");
    expect(typeof fetchArchitectureLayers).toBe("function");
  });

  it("constructs correct query parameters for PIML requests", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        piml: { physical_consistency_score: 98.8 },
      }),
    });
    global.fetch = mockFetch;

    const res = await fetchPIMLComparison({
      temperatureC: 32.5,
      relativeHumidityPct: 80,
      surfacePressureHpa: 1009,
      elevationM: 15,
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain("/advanced-ml/piml-comparison");
    expect(calledUrl).toContain("temperature_c=32.5");
    expect(calledUrl).toContain("relative_humidity_pct=80");
    expect(calledUrl).toContain("surface_pressure_hpa=1009");
    expect(calledUrl).toContain("elevation_m=15");
    expect(res.piml.physical_consistency_score).toBe(98.8);
  });

  it("constructs correct query parameters for 1 km downscaling requests", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        source_resolution: "Coarse NWP",
        downscaled_result: { temperature_c: 29.5 },
      }),
    });
    global.fetch = mockFetch;

    const res = await fetchDownscaling({
      coarseTemp: 32.0,
      coarsePrecip: 15.0,
      targetElevationM: 400.0,
      distanceToCoastKm: 12.0,
      landUse: "urban",
    });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain("/advanced-ml/downscaling");
    expect(calledUrl).toContain("coarse_temp=32");
    expect(calledUrl).toContain("target_elevation_m=400");
    expect(calledUrl).toContain("distance_to_coast_km=12");
    expect(calledUrl).toContain("land_use=urban");
    expect(res.downscaled_result.temperature_c).toBe(29.5);
  });

  it("constructs correct body for natural language weather queries", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        query: "What is the probability of heavy rain in Chennai tomorrow?",
        answer: "The probability of heavy rain exceeding 35mm is 14%.",
      }),
    });
    global.fetch = mockFetch;

    const res = await queryNaturalLanguageWeather({
      query: "What is the probability of heavy rain in Chennai tomorrow?",
      locationId: "chennai",
      currentTemp: 31.0,
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [calledUrl, options] = mockFetch.mock.calls[0];
    expect(calledUrl).toContain("/advanced-ml/nlp-query");
    expect(options.method).toBe("POST");
    const parsedBody = JSON.parse(options.body);
    expect(parsedBody.query).toContain("probability of heavy rain");
    expect(parsedBody.location_id).toBe("chennai");
    expect(res.answer).toContain("14%");
  });

  it("queries 5-layer architecture, regional learning, and air quality endpoints", async () => {
    const mockFetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/architecture-layers")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ layers: [{ layer_number: 1, layer_name: "Multimodal Data Ingestion" }] }),
        });
      }
      if (url.includes("/regional-multimodal")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ name: "Coromandel Coastal Corridor", regional_transfer_mae_c: 0.88 }),
        });
      }
      if (url.includes("/air-quality-intelligence")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ forecast_naqi: 108, category: "Moderate" }),
        });
      }
      if (url.includes("/horizon-strategy")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ horizons: [{ horizon_range: "0–6 hours" }] }),
        });
      }
      if (url.includes("/model-evaluation-drift")) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ benchmark_comparisons: [{ model_variant: "Persistence" }] }),
        });
      }
      return Promise.resolve({ ok: true, json: async () => ({}) });
    });
    global.fetch = mockFetch;

    const layers = await fetchArchitectureLayers();
    expect(layers.layers[0].layer_name).toBe("Multimodal Data Ingestion");

    const regional = await fetchRegionalMultimodal("tamil_nadu_coast");
    expect(regional.name).toContain("Coromandel");

    const aqi = await fetchAirQualityIntelligence({ surfaceWindKmh: 14.0 });
    expect(aqi.forecast_naqi).toBe(108);

    const horizon = await fetchHorizonStrategy();
    expect(horizon.horizons.length).toBe(1);

    const evalDrift = await fetchModelEvaluationAndDrift("chennai");
    expect(evalDrift.benchmark_comparisons.length).toBe(1);
  });
});
