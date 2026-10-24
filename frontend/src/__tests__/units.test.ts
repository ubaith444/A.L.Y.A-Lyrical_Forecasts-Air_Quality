import { describe, it, expect } from "vitest";
import {
  formatTemperature,
  formatWindSpeed,
  formatPrecipitation,
  windDegreeToDirection,
} from "../lib/units";

describe("Unit conversion and formatting", () => {
  it("formats temperature correctly in Celsius and Fahrenheit", () => {
    expect(formatTemperature(25, "C")).toBe("25°");
    expect(formatTemperature(25, "F")).toBe("77°");
    expect(formatTemperature(0, "C")).toBe("0°");
    expect(formatTemperature(0, "F")).toBe("32°");
  });

  it("never converts missing temperature to zero", () => {
    expect(formatTemperature(null, "C")).toBe("—");
    expect(formatTemperature(undefined, "C")).toBe("—");
  });

  it("formats wind speed in km/h, m/s, and mph", () => {
    expect(formatWindSpeed(36, "km/h")).toBe("36 km/h");
    expect(formatWindSpeed(36, "m/s")).toBe("10.0 m/s");
    expect(formatWindSpeed(36, "mph")).toBe("22.4 mph");
    expect(formatWindSpeed(null)).toBe("—");
  });

  it("converts wind degrees to compass directions", () => {
    expect(windDegreeToDirection(0)).toBe("N");
    expect(windDegreeToDirection(90)).toBe("E");
    expect(windDegreeToDirection(180)).toBe("S");
    expect(windDegreeToDirection(270)).toBe("W");
    expect(windDegreeToDirection(null)).toBe("—");
  });

  it("formats precipitation volume without silent zero conversion", () => {
    expect(formatPrecipitation(12.4, "mm")).toBe("12.4 mm");
    expect(formatPrecipitation(25.4, "in")).toBe("1.00 in");
    expect(formatPrecipitation(null, "mm")).toBe("—");
  });
});
