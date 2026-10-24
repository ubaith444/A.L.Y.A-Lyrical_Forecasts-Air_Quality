import { describe, it, expect, vi } from "vitest";
import {
  fetchPredictionSystemsOverview,
  fetchCalibratedForecast,
  fetchClimateAnomalies,
  fetchClimateProjections,
} from "../lib/api";

describe("3-System AI/ML Prediction Architecture API Client", () => {
  it("defines prediction systems API client methods correctly", () => {
    expect(typeof fetchPredictionSystemsOverview).toBe("function");
    expect(typeof fetchCalibratedForecast).toBe("function");
    expect(typeof fetchClimateAnomalies).toBe("function");
    expect(typeof fetchClimateProjections).toBe("function");
  });

  it("constructs correct query parameters for System B anomaly requests", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        system: "System B",
        composite_anomaly_score: 42.5,
      }),
    });
    global.fetch = mockFetch;

    const res = await fetchClimateAnomalies({
      locationId: "chennai",
      temp: 36.5,
      rainMonth: 40,
      dryDays: 14,
      month: 5,
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain("/api/v1/ml/anomalies");
    expect(calledUrl).toContain("location_id=chennai");
    expect(calledUrl).toContain("temp=36.5");
    expect(calledUrl).toContain("rain_month=40");
    expect(calledUrl).toContain("dry_days=14");
    expect(res.composite_anomaly_score).toBe(42.5);
  });

  it("constructs correct query parameters for System C INDRA-CMIP6 projections", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        system: "System C",
        scenarios: { ssp245: {} },
      }),
    });
    global.fetch = mockFetch;

    const res = await fetchClimateProjections({
      locationId: "chennai",
      scenario: "ssp245",
      epoch: "2041_2060",
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain("/api/v1/ml/projections");
    expect(calledUrl).toContain("location_id=chennai");
    expect(calledUrl).toContain("scenario=ssp245");
    expect(calledUrl).toContain("epoch=2041_2060");
    expect(res.system).toBe("System C");
  });
});
