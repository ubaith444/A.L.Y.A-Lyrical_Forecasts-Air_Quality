import { describe, it, expect, vi } from "vitest";
import {
  fetchEarlyWarningAlerts,
  fetchRegionalEarlyWarning,
  simulateAlertDispatch,
  fetchAlertHistory,
} from "../lib/api";

describe("Intelligent Early-Warning & Disaster Alert System Frontend APIs", () => {
  it("defines all early warning API methods", () => {
    expect(typeof fetchEarlyWarningAlerts).toBe("function");
    expect(typeof fetchRegionalEarlyWarning).toBe("function");
    expect(typeof simulateAlertDispatch).toBe("function");
    expect(typeof fetchAlertHistory).toBe("function");
  });

  it("constructs correct query parameters for location hazard alert request", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        system: "A.L.Y.A Intelligent Multi-Hazard Early Warning System",
        overall_alert: { level: 2, level_title: "Level 2 — Warning" },
      }),
    });
    global.fetch = mockFetch;

    const res = await fetchEarlyWarningAlerts({
      locationId: "cuddalore",
      simPrecip24h: 120,
      simWindGust: 65,
      simTsunamiActive: false,
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const url = mockFetch.mock.calls[0][0];
    expect(url).toContain("/api/v1/early-warning/alerts");
    expect(url).toContain("location_id=cuddalore");
    expect(url).toContain("sim_precip_24h=120");
    expect(url).toContain("sim_wind_gust=65");
    expect(res.overall_alert.level).toBe(2);
  });

  it("handles simulated alert dispatch and duplicate suppression response", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        dispatch_id: "test-uuid-1234",
        suppressed: false,
        channels: ["dashboard", "push", "sms", "email"],
      }),
    });
    global.fetch = mockFetch;

    const res = await simulateAlertDispatch({
      hazard: "lightning",
      level: 2,
      locationId: "madurai",
      headline: "Severe Lightning & Thunderstorm Approaching Madurai",
      instructions: ["Seek indoor shelter."],
    });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const options = mockFetch.mock.calls[0][1];
    expect(options.method).toBe("POST");
    expect(JSON.parse(options.body).hazard).toBe("lightning");
    expect(res.suppressed).toBe(false);
  });
});
