import { describe, it, expect } from "vitest";
import { getCPCBConfig, getUSEPAConfig } from "../lib/aqi-utils";

describe("AQI utilities", () => {
  it("maps numeric CPCB NAQI to correct official category and colors", () => {
    const good = getCPCBConfig(35);
    expect(good.category).toBe("Good");
    expect(good.badgeHex).toBe("#10B981");

    const sat = getCPCBConfig(85);
    expect(sat.category).toBe("Satisfactory");

    const mod = getCPCBConfig(160);
    expect(mod.category).toBe("Moderate");

    const poor = getCPCBConfig(240);
    expect(poor.category).toBe("Poor");

    const vpoor = getCPCBConfig(350);
    expect(vpoor.category).toBe("Very Poor");

    const severe = getCPCBConfig(460);
    expect(severe.category).toBe("Severe");
  });

  it("handles null or undefined as unavailable", () => {
    const unavail = getCPCBConfig(null);
    expect(unavail.category).toBe("Unavailable");
  });

  it("maps US EPA AQI values independently without confusing standards", () => {
    const epa = getUSEPAConfig(125);
    expect(epa.category).toBe("Unhealthy for Sensitive Groups");
  });
});
