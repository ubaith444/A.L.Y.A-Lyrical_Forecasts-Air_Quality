import { describe, it, expect } from "vitest";
import { generateLyricalSynopsis, getWeatherConditionLabel } from "../lib/lyrical";

describe("Lyrical synopsis generator", () => {
  it("generates rain-focused lyrical descriptions for rainy conditions", () => {
    const text = generateLyricalSynopsis({ precipitation: 2.5, weatherCode: 61 });
    expect(text).toContain("rain");
  });

  it("generates monsoon description for heavy rainfall", () => {
    const text = generateLyricalSynopsis({ precipitation: 12.0 });
    expect(text).toContain("Monsoon rains");
  });

  it("generates radiant description for hot sunny weather", () => {
    const text = generateLyricalSynopsis({ temperature: 38.0, weatherCode: 0, cloudCover: 5 });
    expect(text).toContain("Golden brilliance");
  });

  it("maps weather codes to clean descriptive labels", () => {
    expect(getWeatherConditionLabel(0)).toBe("Clear Sky");
    expect(getWeatherConditionLabel(2)).toBe("Partly Cloudy");
    expect(getWeatherConditionLabel(61)).toBe("Slight Rain");
    expect(getWeatherConditionLabel(95)).toBe("Thunderstorm");
    expect(getWeatherConditionLabel(null)).toBe("Conditions Available");
  });
});
