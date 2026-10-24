import { describe, it, expect } from "vitest";
import {
  generateWeatherStory,
  computeBestTimeToGo,
  computeRainAroundYou,
  computeWeatherMemory,
  getLivingAtmosphere,
} from "../lib/intelligence";
import { HourlyForecastItem, DailyForecastItem, CurrentConditions } from "../types/weather";

describe("A.L.Y.A Meteorological Intelligence Suite", () => {
  const mockCurrent: CurrentConditions = {
    time: "2026-10-24T12:00:00Z",
    values: {
      temperature_2m: 31.0,
      apparent_temperature: 36.5,
      relative_humidity_2m: 75,
      precipitation: 0.0,
      weather_code: 1,
    },
    units: { temperature_2m: "°C" },
  };

  const mockHourly: HourlyForecastItem[] = Array.from({ length: 24 }).map((_, idx) => ({
    time: `2026-10-24T${String(idx).padStart(2, "0")}:00:00Z`,
    temperature_2m: 25 + (idx > 14 ? 30 - idx : idx * 0.5),
    precipitation_probability: idx === 17 ? 65 : 10,
    precipitation: idx === 17 ? 2.5 : 0.0,
    relative_humidity_2m: 70,
  }));

  const mockDaily: DailyForecastItem[] = [
    {
      time: "2026-10-24",
      temperature_2m_max: 33.5,
      temperature_2m_min: 24.0,
      precipitation_sum: 2.5,
      precipitation_probability_max: 65,
      sunrise: "2026-10-24T06:04",
      sunset: "2026-10-24T17:52",
    },
  ];

  it("generates a unified daily Weather Story with 4 distinct day phases", () => {
    const story = generateWeatherStory(mockCurrent, mockHourly, mockDaily);
    expect(story.headline).toContain("evening showers");
    expect(story.phases).toHaveLength(4);
    expect(story.phases.map((p) => p.id)).toEqual(["morning", "afternoon", "evening", "night"]);
    expect(story.comparisonWithYesterday.description).toContain("yesterday");
  });

  it("computes The Best Time to Go for exercise, transit, and daylight", () => {
    const decisions = computeBestTimeToGo(mockHourly, mockDaily, null);
    expect(decisions.exerciseWindow.bestTime).toContain("AM");
    expect(decisions.commuteWindow.eveningRainRisk).toBe(true);
    expect(decisions.sunTimes.sunrise).toContain("06:04 AM");
    expect(decisions.sunTimes.sunset).toContain("05:52 PM");
  });

  it("computes Rain Around You 12-hour timeline with expected volume", () => {
    const rain = computeRainAroundYou(mockHourly);
    expect(rain.items).toHaveLength(12);
    expect(rain.maxRainProb).toBeGreaterThanOrEqual(10);
    expect(rain.isReliableRadar).toBe(true);
  });

  it("computes Weather Memory and Monsoon Watch baselines", () => {
    const memory = computeWeatherMemory(mockCurrent, mockDaily);
    expect(memory.tempComparison.text).toContain("yesterday");
    expect(memory.monsoonWatch.phase).toContain("Monsoon");
    expect(memory.forecastVsActual.accuracyPct).toBeGreaterThan(90);
  });

  it("returns living atmosphere according to current time and conditions", () => {
    const atmosphere = getLivingAtmosphere();
    expect(["morning", "day", "evening", "night"]).toContain(atmosphere.mode);
    expect(atmosphere.ambientClass).toContain("atmospheric-");
  });
});
