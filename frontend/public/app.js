/**
 * Tamil Nadu Climate & Forecast Intelligence Platform
 * Commercial SaaS Application Controller (app.js)
 * Strict Light Mode Only, Multi-Font System, Zero Emojis, CSV Exports,
 * Leaflet Spatial Engine & Chart.js Visualizations.
 */

// Resolve production API base URL from Next.js environment or meta tag
const API_BASE = (() => {
  if (typeof window !== "undefined") {
    if (window.__ENV__ && window.__ENV__.NEXT_PUBLIC_API_BASE_URL) {
      return window.__ENV__.NEXT_PUBLIC_API_BASE_URL.replace(/\/$/, "");
    }
    const metaTag = document.querySelector('meta[name="api-base-url"]');
    if (metaTag && metaTag.getAttribute("content")) {
      return metaTag.getAttribute("content").replace(/\/$/, "");
    }
    const origin = window.location.origin;
    if (origin.includes("5500") || origin.includes("5173") || origin.includes("3000") || origin.includes("localhost") || origin.includes("127.0.0.1")) {
      return "http://127.0.0.1:8000";
    }
  }
  return "";
})();

// Global Application State
let currentDistrictId = "chennai";
let allDistricts = [];
let allRisks = [];
let comparisonDistricts = ["chennai", "coimbatore", "madurai", "salem"];

// Hourly Chart State
let hourlyFilter = "temp"; // 'temp' | 'rain' | 'humidity' | 'wind'
let hourlyChartType = "line"; // 'line' | 'area' | 'bar'
let hourlyHours = 48; // 24 | 48
let cachedHourlyData = null;

// Daily Forecast State
let forecastModeDays = 7; // 7 | 14
let cachedDailyData = null;

// Leaflet Map State
let leafletMap = null;
let geojsonLayer = null;
let markersLayerGroup = null;
let rawGeoJson = null;
let mapWeatherData = null;
let currentMapVariable = "temperature";

// Chart.js Instances
let hourlyChartInstance = null;
let dailyTempChartInstance = null;
let dailyRainChartInstance = null;
let districtCompareChartInstance = null;
let tempTrendsChartInstance = null;
let monthlyClimChartInstance = null;
let seasonalRainfallChartInstance = null;
let backtestChartInstance = null;
let cachedPhase3Rankings = [];

// In-Memory Client Cache with TTL (10 minutes)
const clientCache = new Map();
function getCached(key) {
  const item = clientCache.get(key);
  if (!item) return null;
  if (Date.now() > item.expiry) {
    clientCache.delete(key);
    return null;
  }
  return item.data;
}
function setCached(key, data, ttlMs = 10 * 60 * 1000) {
  clientCache.set(key, { data, expiry: Date.now() + ttlMs });
}

// Inline SVG Icon Provider (Strict Zero Emojis)
const SVG_ICONS = {
  sun: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`,
  cloudSun: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="M20 12h2"></path><path d="m19.07 4.93-1.41 1.41"></path><path d="M15.947 12.65a4 4 0 0 0-5.925-4.128"></path><path d="M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6z"></path></svg>`,
  cloud: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"></path></svg>`,
  cloudRain: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"></path><path d="M16 14v6"></path><path d="M8 14v6"></path><path d="M12 16v6"></path></svg>`,
  cloudDrizzle: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"></path><path d="M8 19v1"></path><path d="M8 14v1"></path><path d="M12 21v1"></path><path d="M12 16v1"></path><path d="M16 19v1"></path><path d="M16 14v1"></path></svg>`,
  cloudLightning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 16.326A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 .5 8.973"></path><path d="m13 12-3 5h4l-3 5"></path></svg>`,
  moon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"></path></svg>`,
  heat: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"></path></svg>`
};

function getWeatherConditionSvg(code, isDay = true, rainMm = 0, rainProb = 0) {
  if (rainMm >= 15 || rainProb >= 75) return SVG_ICONS.cloudLightning;
  if (rainMm > 0 || rainProb >= 40) return SVG_ICONS.cloudRain;
  if (!isDay) return SVG_ICONS.moon;
  if (code >= 3) return SVG_ICONS.cloud;
  if (code >= 1) return SVG_ICONS.cloudSun;
  return SVG_ICONS.sun;
}

// ==============================================================================
// 1. Application Initialization & URL State
// ==============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  // Read URL query parameter for shareable dashboard selection
  const urlParams = new URLSearchParams(window.location.search);
  const districtParam = urlParams.get("district");
  if (districtParam) {
    currentDistrictId = districtParam.toLowerCase().trim();
  }

  setupLayoutControls();
  setupEventListeners();
  initLeafletMap();

  try {
    await loadDistricts();
    await loadStatewideRisks();
    await loadMapWeatherData(currentMapVariable);
    await loadDistrictDashboard(currentDistrictId);
    await loadComparisonDashboard();
    initPhase3ClimateAnalytics();
    initPhase4MLEvaluation();
    initPhase5RiskIntelligence();
    initOperationalIntelligence();
  } catch (err) {
    console.error("Initialization error:", err);
    showToast("Error loading initial meteorological data.", "critical");
  }
});

// Setup sidebar, top navigation, and layout interactions
function setupLayoutControls() {
  const appShell = document.getElementById("appShell");
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
  const mobileMenuBtn = document.getElementById("mobileMenuBtn");

  // Sidebar Desktop Collapse Toggle
  if (sidebarToggleBtn && appShell) {
    sidebarToggleBtn.addEventListener("click", () => {
      appShell.classList.toggle("sidebar-collapsed");
      setTimeout(() => {
        if (leafletMap) leafletMap.invalidateSize();
      }, 300);
    });
  }

  // Mobile Slide-Out Drawer Toggle
  if (mobileMenuBtn && appShell) {
    mobileMenuBtn.addEventListener("click", () => {
      appShell.classList.toggle("sidebar-mobile-open");
    });
  }

  // Sidebar Navigation Links
  const navLinks = document.querySelectorAll(".nav-link");
  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      navLinks.forEach(l => l.classList.remove("active"));
      link.classList.add("active");
      if (appShell) appShell.classList.remove("sidebar-mobile-open");
    });
  });
}

function setupEventListeners() {
  const districtSelect = document.getElementById("districtSelect");
  const quickCitiesPills = document.getElementById("quickCitiesPills");
  const refreshAllBtn = document.getElementById("refreshAllBtn");
  const exportCompareCsvBtn = document.getElementById("exportCompareCsvBtn");
  const exportClimateCsvBtn = document.getElementById("exportClimateCsvBtn");

  // Topbar District Selector Dropdown
  if (districtSelect) {
    districtSelect.addEventListener("change", (e) => {
      selectDistrict(e.target.value);
    });
  }

  // Quick Select Major Cities Chips
  if (quickCitiesPills) {
    quickCitiesPills.addEventListener("click", (e) => {
      const btn = e.target.closest(".city-chip");
      if (!btn) return;
      const dId = btn.getAttribute("data-district");
      selectDistrict(dId);
    });
  }

  // Refresh Button with Animation
  if (refreshAllBtn) {
    refreshAllBtn.addEventListener("click", async () => {
      refreshAllBtn.classList.add("spinning");
      clientCache.clear();
      showToast(`Refreshing meteorological feeds for ${currentDistrictId.toUpperCase()}...`);
      await loadDistrictDashboard(currentDistrictId);
      await loadMapWeatherData(currentMapVariable);
      setTimeout(() => refreshAllBtn.classList.remove("spinning"), 600);
      showToast("Data feeds successfully updated.", "success");
    });
  }

  // Hourly Metric Filters (Temperature, Rain & Prob, Humidity, Wind)
  const hourlyFilterBtns = document.querySelectorAll("[data-hourly-filter]");
  hourlyFilterBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      hourlyFilterBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      hourlyFilter = btn.getAttribute("data-hourly-filter");
      renderHourlyChart();
    });
  });

  // Hourly Chart Type (Line, Area, Bar)
  const hourlyTypeBtns = document.querySelectorAll("[data-chart-type]");
  hourlyTypeBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      hourlyTypeBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      hourlyChartType = btn.getAttribute("data-chart-type");
      renderHourlyChart();
    });
  });

  // Hourly Horizon (24h vs 48h)
  const btn24 = document.getElementById("hourly24Btn");
  const btn48 = document.getElementById("hourly48Btn");
  if (btn24 && btn48) {
    btn24.addEventListener("click", () => {
      btn24.classList.add("active");
      btn48.classList.remove("active");
      hourlyHours = 24;
      loadHourlyForecast(currentDistrictId);
    });
    btn48.addEventListener("click", () => {
      btn48.classList.add("active");
      btn24.classList.remove("active");
      hourlyHours = 48;
      loadHourlyForecast(currentDistrictId);
    });
  }

  // Daily 7 vs 14 day toggle
  const btn7 = document.getElementById("btn7Day");
  const btn14 = document.getElementById("btn14Day");
  if (btn7 && btn14) {
    btn7.addEventListener("click", () => {
      btn7.classList.add("active");
      btn14.classList.remove("active");
      forecastModeDays = 7;
      loadDailyForecast(currentDistrictId);
    });
    btn14.addEventListener("click", () => {
      btn14.classList.add("active");
      btn7.classList.remove("active");
      forecastModeDays = 14;
      loadDailyForecast(currentDistrictId);
    });
  }

  // Map Variable Selectors
  const mapVarPills = document.querySelectorAll("#mapVarPills .segmented-btn");
  mapVarPills.forEach(p => {
    p.addEventListener("click", () => {
      mapVarPills.forEach(b => b.classList.remove("active"));
      p.classList.add("active");
      currentMapVariable = p.getAttribute("data-variable");
      loadMapWeatherData(currentMapVariable);
    });
  });

  // Map Layer Toggles
  const toggleDistBoundaries = document.getElementById("toggleDistBoundaries");
  const toggleDistMarkers = document.getElementById("toggleDistMarkers");

  if (toggleDistBoundaries) {
    toggleDistBoundaries.addEventListener("change", (e) => {
      if (geojsonLayer) {
        if (e.target.checked) leafletMap.addLayer(geojsonLayer);
        else leafletMap.removeLayer(geojsonLayer);
      }
    });
  }

  if (toggleDistMarkers) {
    toggleDistMarkers.addEventListener("change", (e) => {
      if (markersLayerGroup) {
        if (e.target.checked) leafletMap.addLayer(markersLayerGroup);
        else leafletMap.removeLayer(markersLayerGroup);
      }
    });
  }

  // Map Reset & Fullscreen
  const mapResetBtn = document.getElementById("mapResetViewBtn");
  if (mapResetBtn) {
    mapResetBtn.addEventListener("click", () => {
      if (leafletMap) leafletMap.setView([11.1271, 78.6569], 7);
    });
  }

  const mapFullscreenBtn = document.getElementById("mapFullscreenBtn");
  if (mapFullscreenBtn) {
    mapFullscreenBtn.addEventListener("click", () => {
      const el = document.getElementById("tnLeafletMap");
      if (!document.fullscreenElement) {
        el.requestFullscreen().catch(err => alert("Fullscreen error: " + err.message));
      } else {
        document.exitFullscreen();
      }
    });
  }

  // Map Search Input
  const mapSearchInput = document.getElementById("mapDistrictSearch");
  const mapSearchGoBtn = document.getElementById("mapSearchGoBtn");
  if (mapSearchGoBtn && mapSearchInput) {
    const doMapSearch = () => {
      const q = mapSearchInput.value.toLowerCase().trim();
      if (!q) return;
      const target = allDistricts.find(d => d.name.toLowerCase().includes(q) || d.id.includes(q));
      if (target && leafletMap) {
        leafletMap.flyTo([target.lat, target.lon], 9, { duration: 1.2 });
        updateMapInspectorPanel(target.id);
        showToast(`Centered on ${target.name} district.`);
      }
    };
    mapSearchGoBtn.addEventListener("click", doMapSearch);
    mapSearchInput.addEventListener("keydown", (e) => { if (e.key === "Enter") doMapSearch(); });
  }

  // Map Inspector Select Button
  const mapPanelSelectBtn = document.getElementById("mapPanelSelectBtn");
  if (mapPanelSelectBtn) {
    mapPanelSelectBtn.addEventListener("click", () => {
      const distId = mapPanelSelectBtn.getAttribute("data-district-id") || currentDistrictId;
      selectDistrict(distId);
      document.getElementById("overview")?.scrollIntoView({ behavior: "smooth" });
    });
  }

  // Sector Impacts Tab switching
  const tabs = document.querySelectorAll(".segmented-btn[data-tab]");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      tab.classList.add("active");
      const targetPane = document.getElementById(tab.getAttribute("data-tab"));
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Comparison Add District Dropdown
  const compareDistrictAddSelect = document.getElementById("compareDistrictAddSelect");
  if (compareDistrictAddSelect) {
    compareDistrictAddSelect.addEventListener("change", (e) => {
      const val = e.target.value;
      if (!val) return;
      if (comparisonDistricts.includes(val)) {
        showToast(`${val.toUpperCase()} is already selected for comparison.`, "warning");
        e.target.value = "";
        return;
      }
      if (comparisonDistricts.length >= 4) {
        showToast("Maximum 4 districts can be compared simultaneously.", "warning");
        e.target.value = "";
        return;
      }
      comparisonDistricts.push(val);
      e.target.value = "";
      renderCompareChips();
      loadComparisonDashboard();
      showToast(`Added ${val.toUpperCase()} to comparison matrix.`, "success");
    });
  }

  // Export Comparison CSV
  if (exportCompareCsvBtn) {
    exportCompareCsvBtn.addEventListener("click", exportComparisonCsv);
  }

  // Export Climate Normals CSV
  if (exportClimateCsvBtn) {
    exportClimateCsvBtn.addEventListener("click", exportClimateNormalsCsv);
  }

  // Search in Risk Radar Table
  const riskTableSearch = document.getElementById("riskTableSearch");
  const riskTableBody = document.getElementById("riskTableBody");
  if (riskTableSearch && riskTableBody) {
    let debounceTimer;
    riskTableSearch.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        const q = e.target.value.toLowerCase().trim();
        const rows = riskTableBody.querySelectorAll("tr");
        rows.forEach(r => {
          const text = r.innerText.toLowerCase();
          r.style.display = text.includes(q) ? "" : "none";
        });
      }, 200);
    });
  }
}

// Central District Selector Action
function selectDistrict(districtId) {
  currentDistrictId = districtId;

  // Sync Topbar Dropdown
  const districtSelect = document.getElementById("districtSelect");
  if (districtSelect && districtSelect.value !== districtId) {
    districtSelect.value = districtId;
  }

  // Sync Quick Cities Chips
  document.querySelectorAll("#quickCitiesPills .city-chip").forEach(chip => {
    chip.classList.toggle("active", chip.getAttribute("data-district") === districtId);
  });

  // Update Breadcrumb & URL
  const meta = allDistricts.find(d => d.id === districtId);
  const distName = meta ? meta.name : districtId.toUpperCase();
  document.getElementById("topbarBreadcrumb").textContent = `${distName} Weather Overview`;
  history.replaceState(null, "", `?district=${districtId}`);

  updateMapInspectorPanel(districtId);
  loadDistrictDashboard(districtId);
  showToast(`Dashboard updated for ${distName}.`);
}

// ==============================================================================
// 2. Load Districts Registry (/api/districts)
// ==============================================================================
async function loadDistricts() {
  const cacheKey = "districts_registry";
  let data = getCached(cacheKey);

  if (!data) {
    try {
      const res = await fetch(`${API_BASE}/api/districts`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
      setCached(cacheKey, data, 60 * 60 * 1000);
    } catch (err) {
      console.error("Failed to load districts:", err);
      return;
    }
  }

  allDistricts = data;
  populateDistrictDropdown(allDistricts);
  populateCompareDropdown(allDistricts);
  renderCompareChips();
}

function populateDistrictDropdown(districts) {
  const select = document.getElementById("districtSelect");
  if (!select) return;
  select.innerHTML = "";
  districts.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = `${d.name} (${d.tamil_name || d.id}) · ${d.region}`;
    if (d.id === currentDistrictId) opt.selected = true;
    select.appendChild(opt);
  });
}

function populateCompareDropdown(districts) {
  const select = document.getElementById("compareDistrictAddSelect");
  if (!select) return;
  select.innerHTML = `<option value="">+ Add District to Compare...</option>`;
  districts.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.id;
    opt.textContent = `${d.name} (${d.region})`;
    select.appendChild(opt);
  });
}

// ==============================================================================
// 3. Central District Dashboard Loader
// ==============================================================================
async function loadDistrictDashboard(districtId) {
  updateTimestamp();

  // Find metadata
  const meta = allDistricts.find(d => d.id === districtId);
  if (meta) {
    document.getElementById("metaDistrictBadge").textContent = meta.name;
    document.getElementById("metaRegionBadge").textContent = meta.region;
    document.getElementById("metaCoordsBadge").textContent = `${meta.lat.toFixed(2)}° N, ${meta.lon.toFixed(2)}° E`;
    document.getElementById("metaElevationBadge").textContent = `Elevation: ${meta.elevation_m} m`;
    document.getElementById("metaAnnualRainBadge").textContent = `Annual Normal: ${meta.normal_annual_rainfall_mm} mm`;
  }

  // Parallel asynchronous fetching
  Promise.all([
    loadCurrentWeather(districtId),
    loadHourlyForecast(districtId),
    loadDailyForecast(districtId),
    fetchDualEngineComparison(districtId),
    fetchSectorImpacts(districtId),
    fetchHistoricalClimate(districtId),
    loadAiInsight(districtId),
    loadPhase3ClimateSuite(districtId),
    loadPhase4MLEvaluation(districtId),
    loadPhase5RiskData(districtId),
    fetchComputedGuidance(districtId, currentGuidanceHorizon),
    fetchSectorMatrix(districtId, currentSectorFilter, currentSectorHorizon, currentSectorSort)
  ]).catch(err => console.error("Error loading dashboard data:", err));
}

// ==============================================================================
// 4. Current Weather Overview (/api/weather/current)
// ==============================================================================
async function loadCurrentWeather(districtId) {
  const cacheKey = `weather_current_${districtId}`;
  let data = getCached(cacheKey);

  try {
    if (!data) {
      const res = await fetch(`${API_BASE}/api/weather/current?district=${districtId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
      setCached(cacheKey, data, 10 * 60 * 1000);
    }

    renderCurrentWeather(data);
  } catch (err) {
    console.error("Current weather load error:", err);
  }
}

function renderCurrentWeather(data) {
  // Telemetry status pill in topbar
  const statusPill = document.getElementById("telemetryPill");
  const statusLabel = document.getElementById("telemetryStatusLabel");
  const diffMin = data.data_freshness_minutes || 4;

  if (statusPill && statusLabel) {
    if (data.is_stale || diffMin > 45) {
      statusPill.className = "telemetry-status-pill stale";
      statusLabel.textContent = `Stale Telemetry (${Math.round(diffMin)}m ago)`;
    } else {
      statusPill.className = "telemetry-status-pill";
      statusLabel.textContent = `Operational · Live (${Math.round(diffMin)}m ago)`;
    }
  }

  // Weather Status Badge
  const badgeEl = document.getElementById("currentConditionBadge");
  const textEl = document.getElementById("currentConditionText");
  const descEl = document.getElementById("currentConditionDesc");

  const status = data.status || "Clear";
  textEl.textContent = status;
  descEl.textContent = data.status_description || "Tropical coastal micro-climate conditions.";

  badgeEl.className = "condition-status-badge";
  if (status === "Storm Risk") badgeEl.classList.add("status-storm");
  else if (status === "Rainy") badgeEl.classList.add("status-rainy");
  else if (status === "Hot") badgeEl.classList.add("status-hot");
  else if (status === "Cloudy") badgeEl.classList.add("status-cloudy");
  else badgeEl.classList.add("status-clear");

  // Hero Temp Display
  const t = data.temperature_2m;
  const appT = data.apparent_temperature;
  document.getElementById("currentTemp").textContent = t.toFixed(1);
  document.getElementById("apparentTempRow").textContent = `Feels like ${appT.toFixed(1)} °C`;
  document.getElementById("observationTimestamp").textContent = `Observed: ${data.timestamp ? data.timestamp.replace("T", " ").substring(0, 16) : "Live Telemetry"}`;

  // Today's Summary
  const today = data.today_summary || {};
  document.getElementById("todayMaxTemp").textContent = (today.temp_max ?? (t + 2.5)).toFixed(1);
  document.getElementById("todayMinTemp").textContent = (today.temp_min ?? (t - 4.0)).toFixed(1);
  document.getElementById("todayExpectedRain").textContent = (today.expected_rain_mm ?? 0).toFixed(1);
  document.getElementById("todayRainProb").textContent = today.rain_probability ?? 20;
  document.getElementById("todaySunrise").textContent = today.sunrise || "06:04 AM";
  document.getElementById("todaySunset").textContent = today.sunset || "06:08 PM";

  // 6 KPI Cards
  document.getElementById("kpiTemp").textContent = t.toFixed(1);
  document.getElementById("kpiTempRange").textContent = `Diurnal: ${(today.temp_min ?? (t-4)).toFixed(0)}° / ${(today.temp_max ?? (t+2)).toFixed(0)}°C`;
  const tempPct = Math.min(100, Math.max(0, ((t - 15) / 30) * 100));
  document.getElementById("tempBarFill").style.width = `${tempPct}%`;

  const rh = Math.round(data.relative_humidity_2m);
  document.getElementById("currentHumidity").textContent = rh;
  document.getElementById("humidityBarFill").style.width = `${rh}%`;
  const dewpoint = t - ((100 - rh) / 5);
  document.getElementById("dewpointFooter").textContent = `Dewpoint: ${dewpoint.toFixed(1)} °C`;

  const rain = data.precipitation_mm;
  document.getElementById("currentPrecip").textContent = rain.toFixed(1);
  document.getElementById("rainBarFill").style.width = `${Math.min(100, (rain / 50) * 100)}%`;
  document.getElementById("cloudCoverFooter").textContent = `Cloud Cover: ${Math.round(data.cloud_cover || 20)}%`;

  const wind = data.wind_speed_10m;
  document.getElementById("currentWind").textContent = wind.toFixed(1);
  document.getElementById("windBarFill").style.width = `${Math.min(100, (wind / 50) * 100)}%`;
  document.getElementById("windDirFooter").textContent = `Vector: ${Math.round(data.wind_direction_10m || 80)}° · Gusts: ${(data.wind_gusts_10m || wind * 1.3).toFixed(1)} km/h`;

  const pressure = data.pressure_msl;
  document.getElementById("currentPressure").textContent = pressure.toFixed(1);
  document.getElementById("pressureTrend").textContent = pressure < 1008 ? "Low isobaric trough" : "Stable sea-level isobar";

  const uv = data.uv_index || 0.0;
  document.getElementById("currentUv").textContent = uv.toFixed(1);
  document.getElementById("uvBarFill").style.width = `${Math.min(100, (uv / 12) * 100)}%`;
  let uvDesc = "Low Risk";
  if (uv >= 8) uvDesc = "Very High UV Hazard";
  else if (uv >= 6) uvDesc = "High UV Exposure";
  else if (uv >= 3) uvDesc = "Moderate Exposure Risk";
  document.getElementById("uvExposureFooter").textContent = uvDesc;
}

// ==============================================================================
// 5. Hourly Forecast Trajectory (/api/weather/hourly)
// ==============================================================================
async function loadHourlyForecast(districtId) {
  const cacheKey = `hourly_${districtId}_${hourlyHours}h`;
  let data = getCached(cacheKey);

  try {
    if (!data) {
      const res = await fetch(`${API_BASE}/api/weather/hourly?district=${districtId}&hours=${hourlyHours}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
      setCached(cacheKey, data, 30 * 60 * 1000);
    }

    cachedHourlyData = data;
    renderHourlyChart();
    renderHourlyScrollStrip(data.hourly || []);
  } catch (err) {
    console.error("Hourly forecast load error:", err);
  }
}

function renderHourlyChart() {
  if (!cachedHourlyData || !cachedHourlyData.hourly) return;
  const list = cachedHourlyData.hourly;
  const labels = list.map(h => h.hour_label || h.time.split("T")[1].substring(0, 5));

  const ctx = document.getElementById("hourlyForecastChart");
  if (!ctx) return;
  if (hourlyChartInstance) hourlyChartInstance.destroy();

  const isArea = hourlyChartType === "area";
  const isBar = hourlyChartType === "bar";
  const baseType = isBar ? "bar" : "line";

  let datasets = [];
  let yScales = {};

  if (hourlyFilter === "temp") {
    datasets = [
      {
        label: "Temperature (°C)",
        data: list.map(h => h.temperature),
        borderColor: "#115E59",
        backgroundColor: isArea ? "rgba(17, 94, 89, 0.12)" : (isBar ? "#115E59" : "transparent"),
        fill: isArea,
        tension: 0.35,
        borderWidth: 2.5,
        pointRadius: list.length > 24 ? 1.5 : 2.5
      },
      {
        label: "Feels-Like Temp (°C)",
        data: list.map(h => h.apparent_temperature),
        borderColor: "#D97706",
        backgroundColor: isArea ? "rgba(217, 119, 6, 0.08)" : (isBar ? "#D97706" : "transparent"),
        borderDash: isBar ? [] : [4, 4],
        fill: isArea,
        tension: 0.35,
        borderWidth: 2,
        pointRadius: 0
      }
    ];
    yScales = {
      y: {
        title: { display: true, text: "Degrees Celsius (°C)", font: { family: "'Inter', sans-serif" } },
        grid: { color: "#F1F5F9" }
      }
    };
  } else if (hourlyFilter === "rain") {
    // SEPARATE SCALES for Rainfall mm vs Rain Probability %
    datasets = [
      {
        type: "bar",
        label: "Rainfall Amount (mm)",
        data: list.map(h => h.rain_mm),
        backgroundColor: "#2563EB",
        borderColor: "#1D4ED8",
        borderWidth: 1,
        yAxisID: "yMm",
        borderRadius: 3
      },
      {
        type: "line",
        label: "Precipitation Probability (%)",
        data: list.map(h => h.precipitation_probability_pct),
        borderColor: "#0EA5E9",
        backgroundColor: isArea ? "rgba(14, 165, 233, 0.12)" : "transparent",
        fill: isArea,
        borderWidth: 2,
        yAxisID: "yProb",
        tension: 0.3,
        pointRadius: 2
      }
    ];
    yScales = {
      yMm: {
        type: "linear",
        position: "left",
        title: { display: true, text: "Precipitation Depth (mm)", font: { family: "'Inter', sans-serif" } },
        beginAtZero: true,
        suggestedMax: 15,
        grid: { color: "#F1F5F9" }
      },
      yProb: {
        type: "linear",
        position: "right",
        title: { display: true, text: "Probability (%)", font: { family: "'Inter', sans-serif" } },
        min: 0,
        max: 100,
        grid: { drawOnChartArea: false }
      }
    };
  } else if (hourlyFilter === "humidity") {
    datasets = [
      {
        label: "Relative Humidity (%)",
        data: list.map(h => h.humidity),
        borderColor: "#0284C7",
        backgroundColor: isArea ? "rgba(2, 132, 199, 0.12)" : (isBar ? "#0284C7" : "transparent"),
        fill: isArea,
        tension: 0.35,
        borderWidth: 2.5
      },
      {
        label: "Dewpoint (°C)",
        data: list.map(h => h.dew_point),
        borderColor: "#166534",
        borderDash: isBar ? [] : [4, 4],
        fill: false,
        tension: 0.35,
        borderWidth: 2
      }
    ];
    yScales = {
      y: {
        title: { display: true, text: "Percentage (%) / Dewpoint (°C)", font: { family: "'Inter', sans-serif" } },
        grid: { color: "#F1F5F9" }
      }
    };
  } else if (hourlyFilter === "wind") {
    datasets = [
      {
        label: "Wind Velocity (km/h)",
        data: list.map(h => h.wind_speed),
        borderColor: "#166534",
        backgroundColor: isArea ? "rgba(22, 101, 52, 0.12)" : (isBar ? "#166534" : "transparent"),
        fill: isArea,
        tension: 0.35,
        borderWidth: 2.5
      }
    ];
    yScales = {
      y: {
        title: { display: true, text: "Velocity (km/h)", font: { family: "'Inter', sans-serif" } },
        beginAtZero: true,
        grid: { color: "#F1F5F9" }
      }
    };
  }

  hourlyChartInstance = new Chart(ctx, {
    type: baseType,
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "top",
          labels: { font: { family: "'Inter', sans-serif", weight: 600, size: 12 }, boxWidth: 12 }
        },
        tooltip: {
          backgroundColor: "#172033",
          titleFont: { family: "'Manrope', sans-serif", weight: 700 },
          bodyFont: { family: "'IBM Plex Mono', monospace" },
          padding: 10,
          cornerRadius: 6
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: "'Inter', sans-serif", size: 11 }, maxTicksLimit: 16 }
        },
        ...yScales
      }
    }
  });
}

function renderHourlyScrollStrip(hourlyList) {
  const container = document.getElementById("hourlyIconsStrip");
  if (!container) return;
  container.innerHTML = "";

  hourlyList.forEach(h => {
    const cell = document.createElement("div");
    cell.className = "hourly-cell";
    if (!h.is_day) cell.classList.add("night-cell");
    if (h.is_heavy_rain || h.is_high_temp) cell.classList.add("alert-cell");

    const iconSvg = getWeatherConditionSvg(1, h.is_day, h.rain_mm, h.precipitation_probability_pct);

    cell.innerHTML = `
      <span class="cell-time">${h.hour_label}</span>
      <div class="cell-icon" title="${h.condition}">${iconSvg}</div>
      <span class="cell-temp">${h.temperature.toFixed(0)}°</span>
      <span class="cell-rain">${h.rain_mm > 0 ? h.rain_mm.toFixed(1) + "mm" : (h.precipitation_probability_pct > 0 ? h.precipitation_probability_pct + "%" : "--")}</span>
    `;
    container.appendChild(cell);
  });
}

// ==============================================================================
// 6. Daily Synoptic Forecast Dashboard (/api/weather/daily)
// ==============================================================================
async function loadDailyForecast(districtId) {
  const cacheKey = `daily_${districtId}_${forecastModeDays}d`;
  let data = getCached(cacheKey);

  try {
    if (!data) {
      const res = await fetch(`${API_BASE}/api/weather/daily?district=${districtId}&days=${forecastModeDays}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
      setCached(cacheKey, data, 60 * 60 * 1000);
    }

    cachedDailyData = data;
    renderDailyCards(data.daily || []);
    renderDailyTempSpreadChart(data.daily || []);
    renderDailyPrecipChart(data.daily || []);
  } catch (err) {
    console.error("Daily forecast load error:", err);
  }
}

function renderDailyCards(dailyList) {
  const container = document.getElementById("forecastCardsRow");
  if (!container) return;
  container.innerHTML = "";

  dailyList.forEach((day, index) => {
    const card = document.createElement("div");
    card.className = "daily-card-item";
    if (day.has_warning) card.classList.add("condition-alert");

    const dateObj = new Date(day.date);
    const dayTitle = index === 0 ? "Today" : dateObj.toLocaleDateString("en-US", { weekday: "short" });
    const dateFormatted = dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric" });

    const iconSvg = getWeatherConditionSvg(day.weather_code, true, day.precipitation_sum_mm, day.rain_probability);

    let warningBadge = "";
    if (day.warnings && day.warnings.length > 0) {
      warningBadge = `<div class="dc-alert-tag">${day.warnings[0]}</div>`;
    }

    card.innerHTML = `
      <div>
        <div class="dc-date-title">${dayTitle}</div>
        <div class="dc-date-sub">${dateFormatted}</div>
      </div>
      <div class="dc-icon-slot">${iconSvg}</div>
      <div class="dc-temp-range">
        <span class="dc-tmax">${day.temp_max.toFixed(1)}°</span>
        <span class="dc-tmin">${day.temp_min.toFixed(1)}°</span>
      </div>
      <div class="dc-rain-meta">
        <span>Rain: ${day.precipitation_sum_mm.toFixed(1)} mm</span>
        <span>${day.rain_probability}%</span>
      </div>
      ${warningBadge}
    `;

    card.addEventListener("click", () => {
      showToast(`${dayTitle}: High ${day.temp_max}°C / Low ${day.temp_min}°C &bull; Rain: ${day.precipitation_sum_mm} mm`);
    });

    container.appendChild(card);
  });
}

function renderDailyTempSpreadChart(dailyList) {
  const ctx = document.getElementById("dailyTempRangeChart");
  if (!ctx) return;
  if (dailyTempChartInstance) dailyTempChartInstance.destroy();

  const labels = dailyList.map(d => {
    const dt = new Date(d.date);
    return dt.toLocaleDateString("en-US", { weekday: "short", day: "numeric" });
  });

  dailyTempChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Min Temp (°C)",
          data: dailyList.map(d => d.temp_min),
          backgroundColor: "#93c5fd",
          borderRadius: 3
        },
        {
          label: "Max Temp (°C)",
          data: dailyList.map(d => d.temp_max),
          backgroundColor: "#b91c1c",
          borderRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { font: { family: "'Inter', sans-serif", weight: 600, size: 11 }, boxWidth: 10 } }
      },
      scales: {
        y: {
          title: { display: true, text: "Degrees Celsius (°C)", font: { family: "'Inter', sans-serif" } },
          grid: { color: "#F1F5F9" }
        },
        x: { grid: { display: false }, ticks: { font: { family: "'Inter', sans-serif", size: 10 } } }
      }
    }
  });
}

function renderDailyPrecipChart(dailyList) {
  const ctx = document.getElementById("dailyRainComparisonChart");
  if (!ctx) return;
  if (dailyRainChartInstance) dailyRainChartInstance.destroy();

  const labels = dailyList.map(d => {
    const dt = new Date(d.date);
    return dt.toLocaleDateString("en-US", { weekday: "short", day: "numeric" });
  });

  dailyRainChartInstance = new Chart(ctx, {
    data: {
      labels,
      datasets: [
        {
          type: "bar",
          label: "Precipitation (mm)",
          data: dailyList.map(d => d.precipitation_sum_mm),
          backgroundColor: "#2563EB",
          yAxisID: "yMm",
          borderRadius: 3
        },
        {
          type: "line",
          label: "Probability (%)",
          data: dailyList.map(d => d.rain_probability),
          borderColor: "#0EA5E9",
          backgroundColor: "rgba(14, 165, 233, 0.1)",
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          yAxisID: "yPct",
          pointRadius: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { font: { family: "'Inter', sans-serif", weight: 600, size: 11 }, boxWidth: 10 } }
      },
      scales: {
        yMm: {
          type: "linear",
          position: "left",
          title: { display: true, text: "Depth (mm)", font: { family: "'Inter', sans-serif" } },
          beginAtZero: true,
          grid: { color: "#F1F5F9" }
        },
        yPct: {
          type: "linear",
          position: "right",
          title: { display: true, text: "Likelihood (%)", font: { family: "'Inter', sans-serif" } },
          min: 0,
          max: 100,
          grid: { drawOnChartArea: false }
        },
        x: { grid: { display: false }, ticks: { font: { family: "'Inter', sans-serif", size: 10 } } }
      }
    }
  });
}

// ==============================================================================
// 7. Interactive Tamil Nadu Map (Leaflet)
// ==============================================================================
function initLeafletMap() {
  const container = document.getElementById("tnLeafletMap");
  if (!container || leafletMap) return;

  leafletMap = L.map("tnLeafletMap", {
    center: [11.1271, 78.6569],
    zoom: 7,
    minZoom: 6,
    maxZoom: 12,
    zoomControl: true,
    attributionControl: true
  });

  // CartoDB Positron - Light theme with clear contrast
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> &bull; Tamil Nadu Meteorological Network',
    subdomains: "abcd",
    maxZoom: 19
  }).addTo(leafletMap);

  markersLayerGroup = L.layerGroup().addTo(leafletMap);
}

async function loadMapWeatherData(variable) {
  const cacheKey = `map_weather_${variable}`;
  let data = getCached(cacheKey);

  try {
    if (!data) {
      const res = await fetch(`${API_BASE}/api/map/weather?variable=${variable}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
      setCached(cacheKey, data, 15 * 60 * 1000);
    }

    mapWeatherData = data;
    updateMapLegend(data);

    if (!rawGeoJson) {
      const gRes = await fetch(data.geojson_url || "/static/tamil_nadu_districts.geojson");
      rawGeoJson = await gRes.json();
    }

    renderMapChoropleth(rawGeoJson, data);
    renderMapDistrictMarkers(data);
    updateMapInspectorPanel(currentDistrictId);
  } catch (err) {
    console.error("Map layer load error:", err);
  }
}

// Balanced continuous sequential palette
function getSaaSVariableColor(val, variable) {
  if (val === null || val === undefined) return "#94A3B8";

  if (variable === "temperature") {
    if (val >= 38.0) return "#991b1b";
    if (val >= 35.0) return "#dc2626";
    if (val >= 32.0) return "#ea580c";
    if (val >= 29.0) return "#f59e0b";
    if (val >= 25.0) return "#84cc16";
    return "#10b981";
  } else if (variable === "rainfall") {
    if (val >= 64.5) return "#4c1d95";
    if (val >= 35.0) return "#1e40af";
    if (val >= 15.0) return "#2563eb";
    if (val >= 5.0) return "#38bdf8";
    if (val > 0.0) return "#bae6fd";
    return "#e2e8f0";
  } else if (variable === "humidity") {
    if (val >= 85) return "#0c4a6e";
    if (val >= 75) return "#0284c7";
    if (val >= 65) return "#38bdf8";
    if (val >= 50) return "#84cc16";
    return "#f59e0b";
  } else { // wind
    if (val >= 40.0) return "#b91c1c";
    if (val >= 25.0) return "#d97706";
    if (val >= 15.0) return "#0284c7";
    return "#166534";
  }
}

function renderMapChoropleth(geojson, weatherData) {
  if (!leafletMap) return;
  if (geojsonLayer) leafletMap.removeLayer(geojsonLayer);

  const distMap = weatherData.districts_data || {};
  const variable = weatherData.variable;
  const unit = weatherData.unit;

  const findDistMatch = (geoName) => {
    const norm = geoName.toLowerCase().replace("the ", "").replace("thiru", "tiru");
    for (const [dId, info] of Object.entries(distMap)) {
      if (dId === norm || info.name.toLowerCase().includes(norm) || norm.includes(info.name.toLowerCase())) {
        return { id: dId, ...info };
      }
    }
    if (norm.includes("kanchee")) return { id: "kanchipuram", ...distMap["kanchipuram"] };
    if (norm.includes("kanniya")) return { id: "kanyakumari", ...distMap["kanyakumari"] };
    if (norm.includes("tiruchchi")) return { id: "tiruchirappalli", ...distMap["tiruchirappalli"] };
    return null;
  };

  geojsonLayer = L.geoJSON(geojson, {
    style: (feature) => {
      const geoName = feature.properties.Dist_Name || "";
      const distInfo = findDistMatch(geoName);
      const val = distInfo ? distInfo.value : null;

      return {
        fillColor: getSaaSVariableColor(val, variable),
        weight: 1.5,
        opacity: 1,
        color: "#FFFFFF",
        fillOpacity: 0.75
      };
    },
    onEachFeature: (feature, layer) => {
      const geoName = feature.properties.Dist_Name || "";
      const distInfo = findDistMatch(geoName);
      const valText = distInfo ? `${distInfo.value} ${unit}` : "Missing";
      const targetId = distInfo ? distInfo.id : geoName.toLowerCase();

      layer.bindTooltip(`
        <div style="font-family: var(--font-body); padding: 2px;">
          <strong>${geoName}</strong><br/>
          <span>${variable.toUpperCase()}: <strong>${valText}</strong></span>
        </div>
      `, { sticky: true });

      layer.on({
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({ weight: 2.5, color: "#115E59", fillOpacity: 0.9 });
          l.bringToFront();
        },
        mouseout: (e) => {
          geojsonLayer.resetStyle(e.target);
        },
        click: () => {
          selectDistrict(targetId);
        }
      });
    }
  });

  const toggle = document.getElementById("toggleDistBoundaries");
  if (!toggle || toggle.checked) {
    geojsonLayer.addTo(leafletMap);
  }
}

function renderMapDistrictMarkers(weatherData) {
  if (!markersLayerGroup) return;
  markersLayerGroup.clearLayers();

  const distMap = weatherData.districts_data || {};
  const unit = weatherData.unit;

  Object.entries(distMap).forEach(([dId, info]) => {
    if (!info.lat || !info.lon) return;

    const markerHtml = `
      <div style="
        background: #FFFFFF;
        border: 1px solid #115E59;
        color: #172033;
        font-family: var(--font-body);
        font-size: 10px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        white-space: nowrap;
        text-align: center;
        cursor: pointer;
      ">
        ${info.name}<br/>
        <span style="color: #2563EB; font-family: var(--font-mono); font-size: 9px; font-weight: 700;">${info.value} ${unit}</span>
      </div>
    `;

    const icon = L.divIcon({
      className: "saas-district-marker",
      html: markerHtml,
      iconSize: [80, 26],
      iconAnchor: [40, 13]
    });

    const marker = L.marker([info.lat, info.lon], { icon });
    marker.on("click", () => {
      selectDistrict(dId);
    });

    markersLayerGroup.addLayer(marker);
  });
}

function updateMapLegend(weatherData) {
  const v = weatherData.variable;
  const unit = weatherData.unit;
  document.getElementById("legendVarTitle").textContent = v.charAt(0).toUpperCase() + v.slice(1);
  document.getElementById("legendUnit").textContent = unit;
  document.getElementById("legendMin").textContent = `${weatherData.min_value.toFixed(1)}${unit}`;
  document.getElementById("legendMax").textContent = `${weatherData.max_value.toFixed(1)}${unit}`;
  const mid = ((weatherData.min_value + weatherData.max_value) / 2).toFixed(1);
  document.getElementById("legendMid").textContent = `${mid}${unit}`;
  document.getElementById("legendTimestamp").textContent = `Retrieved: ${new Date(weatherData.timestamp_utc).toLocaleTimeString()}`;

  const bar = document.getElementById("legendGradientBar");
  if (!bar) return;
  if (v === "temperature") {
    bar.style.background = "linear-gradient(to right, #10b981, #84cc16, #f59e0b, #ea580c, #dc2626)";
  } else if (v === "rainfall") {
    bar.style.background = "linear-gradient(to right, #e2e8f0, #bae6fd, #38bdf8, #2563eb, #4c1d95)";
  } else if (v === "humidity") {
    bar.style.background = "linear-gradient(to right, #f59e0b, #84cc16, #38bdf8, #0284c7, #0c4a6e)";
  } else {
    bar.style.background = "linear-gradient(to right, #166534, #0284c7, #d97706, #b91c1c)";
  }
}

function updateMapInspectorPanel(districtId) {
  const meta = allDistricts.find(d => d.id === districtId);
  if (!meta) return;

  document.getElementById("mapPanelName").textContent = meta.name;
  document.getElementById("mapPanelTamilName").textContent = meta.tamil_name || "";
  document.getElementById("mapPanelRegion").textContent = meta.region;
  document.getElementById("mapPanelElevation").textContent = `${meta.elevation_m} m`;
  document.getElementById("mapPanelCoords").textContent = `${meta.lat.toFixed(2)}° N, ${meta.lon.toFixed(2)}° E`;
  document.getElementById("mapPanelNormal").textContent = `${meta.normal_annual_rainfall_mm} mm`;
  document.getElementById("mapPanelNemNormal").textContent = `${meta.nem_normal_mm} mm`;

  const btn = document.getElementById("mapPanelSelectBtn");
  if (btn) btn.setAttribute("data-district-id", districtId);

  if (mapWeatherData && mapWeatherData.districts_data) {
    const distWeather = mapWeatherData.districts_data[districtId];
    if (distWeather) {
      document.getElementById("mapPanelVarLabel").textContent = `${mapWeatherData.variable.toUpperCase()}:`;
      document.getElementById("mapPanelVarVal").textContent = `${distWeather.value} ${mapWeatherData.unit}`;
    }
  }
}

// ==============================================================================
// 8. District Intelligence & Multi-District Comparison (/api/districts/compare)
// ==============================================================================
async function loadComparisonDashboard() {
  const namesParam = comparisonDistricts.join(",");
  const cacheKey = `compare_${namesParam}`;
  let data = getCached(cacheKey);

  try {
    if (!data) {
      const res = await fetch(`${API_BASE}/api/districts/compare?names=${namesParam}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      data = await res.json();
      setCached(cacheKey, data, 10 * 60 * 1000);
    }

    renderComparisonDashboard(data);
  } catch (err) {
    console.error("Comparison load error:", err);
  }
}

function renderCompareChips() {
  const container = document.getElementById("compareChipsBar");
  if (!container) return;
  container.innerHTML = "";

  document.getElementById("compareCounterBadge").textContent = `${comparisonDistricts.length} / 4 Districts Selected`;

  comparisonDistricts.forEach(dId => {
    const meta = allDistricts.find(d => d.id === dId);
    const name = meta ? meta.name : dId.toUpperCase();
    const tag = document.createElement("span");
    tag.className = "compare-tag";
    tag.innerHTML = `
      <span>${name}</span>
      <button class="compare-tag-remove" title="Remove ${name}" data-remove="${dId}">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    `;
    tag.querySelector(".compare-tag-remove").addEventListener("click", () => {
      if (comparisonDistricts.length <= 2) {
        showToast("Comparison requires at least 2 districts.", "warning");
        return;
      }
      comparisonDistricts = comparisonDistricts.filter(id => id !== dId);
      renderCompareChips();
      loadComparisonDashboard();
    });
    container.appendChild(tag);
  });
}

function renderComparisonDashboard(data) {
  // Rankings Pods (Hottest, Wettest, Windiest)
  const rankings = data.rankings || {};
  document.getElementById("rankHottestDist").textContent = rankings.hottest_district || "N/A";
  document.getElementById("rankWettestDist").textContent = rankings.wettest_district || "N/A";
  document.getElementById("rankWindiestDist").textContent = rankings.windiest_district || "N/A";

  // Side-by-side cards
  const grid = document.getElementById("compareCardsGrid");
  if (!grid) return;
  grid.innerHTML = "";

  const list = data.districts || [];
  list.forEach(d => {
    const card = document.createElement("div");
    card.className = "comparison-card";
    if (d.district_id === currentDistrictId) card.classList.add("is-active-district");

    card.innerHTML = `
      <div class="comparison-card-top">
        <div>
          <span class="cc-name">${d.name}</span>
          <span style="display: block; font-size: 0.72rem; color: var(--color-text-muted);">${d.region || "Tamil Nadu"}</span>
        </div>
        <span class="badge-saas ${d.district_id === currentDistrictId ? 'badge-normal' : 'badge-subtle'}">
          ${d.district_id === currentDistrictId ? 'Active' : 'Compared'}
        </span>
      </div>
      <div class="cc-metric-row">
        <span style="color: var(--color-text-secondary);">Temperature:</span>
        <span class="cc-val">${d.temperature_2m !== undefined ? d.temperature_2m.toFixed(1) + " °C" : "--"}</span>
      </div>
      <div class="cc-metric-row">
        <span style="color: var(--color-text-secondary);">Feels-like:</span>
        <span class="cc-val">${d.apparent_temperature !== undefined ? d.apparent_temperature.toFixed(1) + " °C" : "--"}</span>
      </div>
      <div class="cc-metric-row">
        <span style="color: var(--color-text-secondary);">Rainfall (24h):</span>
        <span class="cc-val" style="color: var(--color-ocean);">${d.precipitation_mm !== undefined ? d.precipitation_mm.toFixed(1) + " mm" : "--"}</span>
      </div>
      <div class="cc-metric-row">
        <span style="color: var(--color-text-secondary);">Relative Humidity:</span>
        <span class="cc-val">${d.relative_humidity_2m !== undefined ? Math.round(d.relative_humidity_2m) + " %" : "--"}</span>
      </div>
      <div class="cc-metric-row">
        <span style="color: var(--color-text-secondary);">Wind Velocity:</span>
        <span class="cc-val">${d.wind_speed_10m !== undefined ? d.wind_speed_10m.toFixed(1) + " km/h" : "--"}</span>
      </div>
      <div class="cc-metric-row">
        <span style="color: var(--color-text-secondary);">Elevation:</span>
        <span class="cc-val">${d.elevation_m || 10} m</span>
      </div>
    `;

    grid.appendChild(card);
  });

  renderComparisonBenchmarkChart(list);
}

function renderComparisonBenchmarkChart(districtsList) {
  const ctx = document.getElementById("districtComparisonChart");
  if (!ctx) return;
  if (districtCompareChartInstance) districtCompareChartInstance.destroy();

  const labels = districtsList.map(d => d.name);

  districtCompareChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Temperature (°C)",
          data: districtsList.map(d => d.temperature_2m || 0),
          backgroundColor: "#115E59",
          borderRadius: 3
        },
        {
          label: "Rainfall (mm)",
          data: districtsList.map(d => d.precipitation_mm || 0),
          backgroundColor: "#2563EB",
          borderRadius: 3
        },
        {
          label: "Wind Speed (km/h)",
          data: districtsList.map(d => d.wind_speed_10m || 0),
          backgroundColor: "#166534",
          borderRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { font: { family: "'Inter', sans-serif", weight: 600, size: 11 }, boxWidth: 10 } }
      },
      scales: {
        y: {
          title: { display: true, text: "Metric Value", font: { family: "'Inter', sans-serif" } },
          grid: { color: "#F1F5F9" }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

// Client-Side CSV Export for District Comparison
function exportComparisonCsv() {
  const cacheKey = `compare_${comparisonDistricts.join(",")}`;
  const data = getCached(cacheKey);
  const list = data ? data.districts : [];

  if (!list || list.length === 0) {
    showToast("No comparison data available to export.", "warning");
    return;
  }

  let csv = "District,Region,Temperature_C,Apparent_Temp_C,Rainfall_24h_mm,Relative_Humidity_pct,Wind_Speed_kmh,Elevation_m\n";
  list.forEach(d => {
    csv += `"${d.name}","${d.region || 'Tamil Nadu'}",${d.temperature_2m ?? ''},${d.apparent_temperature ?? ''},${d.precipitation_mm ?? ''},${d.relative_humidity_2m ?? ''},${d.wind_speed_10m ?? ''},${d.elevation_m ?? ''}\n`;
  });

  downloadCsvBlob(csv, "tamil_nadu_district_comparison.csv");
  showToast("Comparison CSV exported successfully.", "success");
}

// Client-Side CSV Export for Climate Normals
function exportClimateNormalsCsv() {
  if (!allDistricts || allDistricts.length === 0) {
    showToast("District dataset not loaded.", "warning");
    return;
  }

  let csv = "District_ID,District_Name,Tamil_Name,Region,Latitude,Longitude,Elevation_m,Annual_Normal_Rain_mm,NEM_Normal_mm,SWM_Normal_mm,Is_Coastal\n";
  allDistricts.forEach(d => {
    csv += `"${d.id}","${d.name}","${d.tamil_name || ''}","${d.region}",${d.lat},${d.lon},${d.elevation_m},${d.normal_annual_rainfall_mm},${d.nem_normal_mm},${d.swm_normal_mm},${d.is_coastal ? 'true' : 'false'}\n`;
  });

  downloadCsvBlob(csv, "tamil_nadu_climate_normals.csv");
  showToast("Climate normals CSV exported successfully.", "success");
}

function downloadCsvBlob(csvContent, fileName) {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ==============================================================================
// 9. Dual-Engine Prediction & Model Attribution (/api/weather/compare)
// ==============================================================================
async function fetchDualEngineComparison(districtId) {
  try {
    const res = await fetch(`${API_BASE}/api/weather/compare/${districtId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const engines = data.engines;

    document.getElementById("apiRainProb").textContent = `${engines.weather_api.rain_probability_pct}%`;
    document.getElementById("apiRainMm").textContent = `${engines.weather_api.rainfall_depth_mm.toFixed(1)} mm`;
    document.getElementById("apiTempMax").textContent = `${engines.weather_api.temperature_max_celsius.toFixed(1)} °C`;
    document.getElementById("apiAccuracy").textContent = `${engines.weather_api.historical_accuracy_pct}%`;

    document.getElementById("mlRainProb").textContent = `${engines.self_trained_model.rain_probability_pct}%`;
    document.getElementById("mlRainMm").textContent = `${engines.self_trained_model.rainfall_depth_mm.toFixed(1)} mm`;
    document.getElementById("mlTempAnomaly").textContent = `${engines.self_trained_model.temperature_anomaly_celsius > 0 ? "+" : ""}${engines.self_trained_model.temperature_anomaly_celsius.toFixed(2)} °C`;
    document.getElementById("mlAccuracy").textContent = `${engines.self_trained_model.historical_accuracy_pct}%`;

    const chipsContainer = document.getElementById("fiChips");
    chipsContainer.innerHTML = "";
    (engines.self_trained_model.key_driving_features || []).forEach(f => {
      const chip = document.createElement("span");
      chip.className = "meta-pill font-mono";
      chip.textContent = `${f.feature} (${f.importance_weight})`;
      chipsContainer.appendChild(chip);
    });

    document.getElementById("consensusTitle").textContent = data.consensus_analysis.rain_consensus 
      ? "Strong Dual-Engine Model Consensus:" 
      : "Dual-Engine Divergence Detected:";
    document.getElementById("consensusDesc").textContent = data.consensus_analysis.summary;
  } catch (err) {
    console.error("Comparison error:", err);
  }
}

// ==============================================================================
// 10. Multi-Sector Impacts & Advisories (/api/impacts)
// ==============================================================================
async function fetchSectorImpacts(districtId) {
  try {
    const res = await fetch(`${API_BASE}/api/impacts/${districtId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    renderSectorBadge("agriRiskBadge", data.agriculture.risk_level);
    renderSectorList("agriCropsList", data.agriculture.monitored_crops);
    renderSectorList("agriAdvisoriesList", data.agriculture.advisories);

    renderSectorBadge("waterRiskBadge", data.water_resources.risk_level);
    renderSectorList("waterReservoirsList", data.water_resources.monitored_reservoirs);
    renderSectorList("waterAdvisoriesList", data.water_resources.advisories);

    renderSectorBadge("transportRiskBadge", data.transport_and_urban.risk_level);
    renderSectorList("transportAdvisoriesList", data.transport_and_urban.advisories);

    renderSectorBadge("healthRiskBadge", data.public_health.risk_level);
    document.getElementById("healthHeatVal").textContent = data.public_health.heat_index_celsius.toFixed(1);
    renderSectorList("healthAdvisoriesList", data.public_health.advisories);
  } catch (err) {
    console.error("Sector impact error:", err);
  }
}

// ==============================================================================
// 11. Climate Intelligence & Monsoon Departure (/api/climate/historical)
// ==============================================================================
async function fetchHistoricalClimate(districtId) {
  try {
    const res = await fetch(`${API_BASE}/api/climate/historical/${districtId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const nem = data.monsoons?.northeast_monsoon?.normal_mm ?? data.nem_normal_mm ?? 450;
    const swm = data.monsoons?.southwest_monsoon?.normal_mm ?? data.swm_normal_mm ?? 320;
    const annual = data.annual_normal_rainfall_mm ?? data.annual_normal_mm ?? 950;
    const summary = data.climatological_summary ?? data.climate_summary ?? "Standard meteorological baseline.";
    const departure = data.monsoons?.northeast_monsoon?.departure_pct ?? data.current_nem_departure_pct ?? 0;
    const imdClass = data.monsoons?.northeast_monsoon?.imd_classification ?? data.imd_performance_category ?? "Normal";

    const nemEl = document.getElementById("nemNormalMm");
    const swmEl = document.getElementById("swmNormalMm");
    const annEl = document.getElementById("annualNormalVal");
    const sumEl = document.getElementById("distClimSummary");

    if (nemEl) nemEl.textContent = `${nem} mm`;
    if (swmEl) swmEl.textContent = `${swm} mm`;
    if (annEl) annEl.textContent = `${annual} mm`;
    if (sumEl) sumEl.textContent = summary;

    const depFill = document.getElementById("nemDepartureFill");
    const depText = document.getElementById("nemDepartureText");
    const depBadge = document.getElementById("nemImdBadge");

    if (depText) {
      depText.textContent = `${departure > 0 ? "+" : ""}${Number(departure).toFixed(1)}% Departure`;
    }
    if (depFill) {
      depFill.style.width = `${Math.min(100, Math.max(10, 50 + Number(departure) / 2))}%`;
    }

    if (depBadge) {
      renderSectorBadge("nemImdBadge", imdClass);
      depBadge.textContent = imdClass;
    }
  } catch (err) {
    console.error("Historical climate error:", err);
  }
}

// ==============================================================================
// 12. AI Meteorological Brief Generator (/api/insights/generate)
// ==============================================================================
async function loadAiInsight(districtId) {
  const proseEl = document.getElementById("aiInsightProse");

  try {
    const res = await fetch(`${API_BASE}/api/insights/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ district_id: districtId })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const drivers = data.synoptic_rationale || data.atmospheric_drivers || "Maritime easterly airflow interacting with regional convective boundaries.";
    const evalText = data.dual_engine_evaluation || data.executive_summary || "Numerical weather prediction tracks closely with self-trained empirical models.";
    const guidance = data.executive_briefing || data.operational_recommendations || "Observe standard monsoon precautions in active agrarian corridors.";

    proseEl.innerHTML = `
      <div><strong>Atmospheric Drivers:</strong> ${drivers}</div>
      <div style="margin: 4px 0;"><strong>Model Evaluation:</strong> ${evalText}</div>
      <div><strong>Operational Guidance:</strong> ${guidance}</div>
    `;
  } catch (err) {
    proseEl.textContent = "Operational telemetry aligned with Numerical Weather Prediction models and local micro-climate stations.";
  }
}

// ==============================================================================
// 13. Statewide 38-District Risk Radar Table (/api/risks)
// ==============================================================================
async function loadStatewideRisks() {
  try {
    const res = await fetch(`${API_BASE}/api/risks`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allRisks = await res.json();
    renderRiskTable(allRisks);
  } catch (err) {
    console.error("Risk radar load error:", err);
  }
}

function renderRiskTable(risks) {
  const tbody = document.getElementById("riskTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  risks.forEach(r => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${r.district_name}</strong> <span style="font-size: 0.74rem; color: var(--color-text-muted);">(${r.tamil_name})</span></td>
      <td>${r.zone}</td>
      <td><span class="badge-saas ${getRiskBadgeClass(r.composite_risk)}">${r.composite_risk}</span></td>
      <td>${formatAlertText(r.alerts.heavy_rain)}</td>
      <td>${formatAlertText(r.alerts.heat_stress)}</td>
      <td>${formatAlertText(r.alerts.flood_landslide)}</td>
      <td>${formatAlertText(r.alerts.dry_spell)}</td>
      <td><button class="btn-saas btn-saas-secondary btn-saas-sm select-from-table-btn" data-district="${r.district_id}">Select</button></td>
    `;

    tr.querySelector(".select-from-table-btn").addEventListener("click", () => {
      selectDistrict(r.district_id);
      document.getElementById("overview")?.scrollIntoView({ behavior: "smooth" });
    });

    tbody.appendChild(tr);
  });
}

function formatAlertText(alertStr) {
  if (!alertStr || alertStr === "None") return `<span style="color: var(--color-text-muted);">None</span>`;
  const str = String(alertStr);
  if (str.includes("Warning") || str.includes("Danger") || str.includes("Severe")) {
    return `<span style="color: var(--color-critical); font-weight: 700;">${str}</span>`;
  }
  return `<span style="color: var(--color-warning); font-weight: 600;">${str}</span>`;
}

function getRiskBadgeClass(level) {
  if (!level || typeof level !== "string") return "badge-normal";
  switch (level.toLowerCase()) {
    case "severe":
    case "large excess":
      return "badge-critical";
    case "warning":
    case "excess":
      return "badge-advisory";
    default:
      return "badge-normal";
  }
}

function renderSectorBadge(elId, level) {
  const el = document.getElementById(elId);
  if (!el) return;
  const safeLevel = level || "Normal";
  el.className = `badge-saas ${getRiskBadgeClass(safeLevel)}`;
  el.textContent = safeLevel;
}

function renderSectorList(elId, items) {
  const el = document.getElementById(elId);
  if (!el) return;
  el.innerHTML = "";
  if (!items || items.length === 0) {
    el.innerHTML = `<li>No active directives.</li>`;
    return;
  }
  items.forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    el.appendChild(li);
  });
}

function updateTimestamp() {
  const el = document.getElementById("lastUpdatedTime");
  if (el) {
    const now = new Date();
    el.textContent = `${now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" })} IST`;
  }
}

// Toast Notifications System
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = "toast-item";
  if (type === "success") toast.style.borderLeftColor = "var(--color-forest)";
  else if (type === "warning") toast.style.borderLeftColor = "var(--color-warning)";
  else if (type === "critical") toast.style.borderLeftColor = "var(--color-critical)";

  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.25s ease";
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 250);
  }, 3200);
}

// ==============================================================================
// 14. Phase 3: Comprehensive Climate Analytics Engine
// ==============================================================================
function initPhase3ClimateAnalytics() {
  // Navigation strip buttons
  const navBtns = document.querySelectorAll(".climate-nav-btn");
  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      navBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const targetView = btn.getAttribute("data-view");
      document.querySelectorAll(".climate-view-pane").forEach(pane => {
        pane.classList.remove("active");
      });
      const targetPane = document.getElementById(targetView);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Filter change events
  const seasonFilter = document.getElementById("trendsSeasonFilter");
  const periodFilter = document.getElementById("trendsPeriodFilter");
  if (seasonFilter) seasonFilter.addEventListener("change", () => fetchPhase3Trends(currentDistrictId));
  if (periodFilter) periodFilter.addEventListener("change", () => fetchPhase3Trends(currentDistrictId));

  // Rankings search
  const rankSearch = document.getElementById("monsoonRankSearch");
  if (rankSearch) {
    rankSearch.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = cachedPhase3Rankings.filter(r =>
        r.district_name.toLowerCase().includes(q) || r.zone.toLowerCase().includes(q)
      );
      renderPhase3MonsoonRankings(filtered);
    });
  }

  setupPhase3ReportGenerator();
  loadPhase3ClimateSuite(currentDistrictId);
}

async function loadPhase3ClimateSuite(districtId) {
  fetchPhase3Trends(districtId);
  fetchPhase3Seasonal(districtId);
  fetchPhase3Anomalies(districtId);
}

// 14.1 Trends & Decadal Trajectory
async function fetchPhase3Trends(districtId) {
  const seasonFilter = document.getElementById("trendsSeasonFilter")?.value || "all";
  const periodFilter = parseInt(document.getElementById("trendsPeriodFilter")?.value || "10", 10);
  const startYr = 2025 - periodFilter;

  try {
    const res = await fetch(`${API_BASE}/api/climate/trends?district=${districtId}&start_year=${startYr}&end_year=2024&season=${seasonFilter}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const distLabel = document.getElementById("trendsDistrictLabel");
    if (distLabel) distLabel.textContent = data.district_name;

    const rateEl = document.getElementById("statWarmingRate");
    const meanTEl = document.getElementById("statMeanTemp");
    const rainyEl = document.getElementById("statRainyDays");
    const rainTrEl = document.getElementById("statRainTrend");

    if (rateEl) rateEl.textContent = `${data.warming_rate_c_per_decade > 0 ? "+" : ""}${data.warming_rate_c_per_decade.toFixed(2)} °C`;
    
    // Calculate averages across yearly trends
    const trends = data.yearly_trends || [];
    if (trends.length > 0) {
      const avgT = trends.reduce((acc, y) => acc + y.mean_temp_celsius, 0) / trends.length;
      const avgRainy = trends.reduce((acc, y) => acc + y.rainy_days, 0) / trends.length;
      if (meanTEl) meanTEl.textContent = `${avgT.toFixed(1)} °C`;
      if (rainyEl) rainyEl.textContent = `${Math.round(avgRainy)} days`;
    }
    if (rainTrEl) rainTrEl.textContent = `${data.rainfall_trend_pct_per_decade > 0 ? "+" : ""}${data.rainfall_trend_pct_per_decade.toFixed(1)}%`;

    renderPhase3TrendsChart(trends, data.warming_rate_c_per_decade);
    renderPhase3MonthlyChart(data.monthly_profile || []);
  } catch (err) {
    console.error("Phase 3 trends fetch error:", err);
  }
}

function renderPhase3TrendsChart(trends, warmingRate) {
  const ctx = document.getElementById("tempTrendsChart");
  if (!ctx) return;
  if (tempTrendsChartInstance) tempTrendsChartInstance.destroy();

  const labels = trends.map(t => t.year);
  const meanTemps = trends.map(t => t.mean_temp_celsius);
  const maxTemps = trends.map(t => t.max_temp_celsius);
  const minTemps = trends.map(t => t.min_temp_celsius);

  // Compute linear trendline for Mean Temp
  const n = trends.length;
  let trendline = [];
  if (n > 1) {
    const xVals = Array.from({ length: n }, (_, i) => i);
    const yVals = meanTemps;
    const xMean = (n - 1) / 2;
    const yMean = yVals.reduce((a, b) => a + b, 0) / n;
    let num = 0, den = 0;
    for (let i = 0; i < n; i++) {
      num += (xVals[i] - xMean) * (yVals[i] - yMean);
      den += (xVals[i] - xMean) ** 2;
    }
    const slope = num / den;
    const intercept = yMean - slope * xMean;
    trendline = xVals.map(x => Number((slope * x + intercept).toFixed(2)));
  }

  tempTrendsChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Mean Temp (°C)",
          data: meanTemps,
          borderColor: "#115E59",
          backgroundColor: "#115E59",
          borderWidth: 2.5,
          tension: 0.25,
          pointRadius: 3
        },
        {
          label: "Max Temp (°C)",
          data: maxTemps,
          borderColor: "#B91C1C",
          backgroundColor: "#B91C1C",
          borderWidth: 1.5,
          borderDash: [3, 3],
          pointRadius: 2
        },
        {
          label: "Min Temp (°C)",
          data: minTemps,
          borderColor: "#0369A1",
          backgroundColor: "#0369A1",
          borderWidth: 1.5,
          borderDash: [3, 3],
          pointRadius: 2
        },
        {
          label: "Decadal Warming Trend",
          data: trendline,
          borderColor: "#D97706",
          backgroundColor: "transparent",
          borderWidth: 2,
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { font: { family: "'Inter', sans-serif", size: 11 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw} °C`
          }
        }
      },
      scales: {
        y: {
          title: { display: true, text: "Degrees Celsius (°C)", font: { family: "'Inter', sans-serif" } },
          grid: { color: "#F1F5F9" }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderPhase3MonthlyChart(monthlyProfile) {
  const ctx = document.getElementById("monthlyClimChart");
  if (!ctx) return;
  if (monthlyClimChartInstance) monthlyClimChartInstance.destroy();

  const labels = monthlyProfile.map(m => m.month_name);
  const normalRain = monthlyProfile.map(m => m.normal_mm);
  const recordedRain = monthlyProfile.map(m => m.recorded_mm);
  const meanTemp = monthlyProfile.map(m => m.mean_temp_celsius);

  monthlyClimChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          type: "bar",
          label: "IMD Normal Rain (mm)",
          data: normalRain,
          backgroundColor: "#E2E8F0",
          borderRadius: 4,
          yAxisID: "yRain"
        },
        {
          type: "bar",
          label: "Recorded Rainfall (mm)",
          data: recordedRain,
          backgroundColor: "#2563EB",
          borderRadius: 4,
          yAxisID: "yRain"
        },
        {
          type: "line",
          label: "Mean Temp (°C)",
          data: meanTemp,
          borderColor: "#D97706",
          borderWidth: 2,
          tension: 0.3,
          pointRadius: 3,
          yAxisID: "yTemp"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { font: { family: "'Inter', sans-serif", size: 11 } } }
      },
      scales: {
        yRain: {
          type: "linear",
          position: "left",
          title: { display: true, text: "Rainfall (mm)", font: { family: "'Inter', sans-serif" } },
          grid: { color: "#F1F5F9" }
        },
        yTemp: {
          type: "linear",
          position: "right",
          title: { display: true, text: "Temperature (°C)", font: { family: "'Inter', sans-serif" } },
          grid: { display: false }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

// 14.2 Seasonal Rainfall & 38-District Rankings
async function fetchPhase3Seasonal(districtId) {
  try {
    const res = await fetch(`${API_BASE}/api/climate/seasonal-rainfall?district=${districtId}&year=2024&season=all`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    cachedPhase3Rankings = data.district_rankings || [];
    renderPhase3MonsoonRankings(cachedPhase3Rankings);

    // Render multi-year seasonal rainfall chart
    const trendsRes = await fetch(`${API_BASE}/api/climate/trends?district=${districtId}&start_year=2015&end_year=2024&season=all`);
    if (trendsRes.ok) {
      const trendsData = await trendsRes.json();
      renderPhase3SeasonalChart(trendsData.yearly_trends || [], trendsData.baseline_normal_mm || 950);
    }
  } catch (err) {
    console.error("Phase 3 seasonal fetch error:", err);
  }
}

function renderPhase3SeasonalChart(trends, baselineNormal) {
  const ctx = document.getElementById("seasonalRainfallChart");
  if (!ctx) return;
  if (seasonalRainfallChartInstance) seasonalRainfallChartInstance.destroy();

  const labels = trends.map(t => t.year);
  const recorded = trends.map(t => t.rainfall_mm);
  const normals = trends.map(() => baselineNormal);

  seasonalRainfallChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Recorded Rainfall (mm)",
          data: recorded,
          backgroundColor: trends.map(t => t.rainfall_departure_pct >= 20 ? "#166534" : (t.rainfall_departure_pct <= -20 ? "#B91C1C" : "#2563EB")),
          borderRadius: 4
        },
        {
          type: "line",
          label: "IMD 30-Yr Normal (mm)",
          data: normals,
          borderColor: "#64748B",
          borderWidth: 2,
          borderDash: [4, 4],
          pointRadius: 0
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { font: { family: "'Inter', sans-serif", size: 11 } } },
        tooltip: {
          callbacks: {
            afterLabel: (ctx) => {
              if (ctx.datasetIndex === 0) {
                const item = trends[ctx.dataIndex];
                return `Departure: ${item.rainfall_departure_pct > 0 ? "+" : ""}${item.rainfall_departure_pct}% (${item.imd_category})`;
              }
              return "";
            }
          }
        }
      },
      scales: {
        y: {
          title: { display: true, text: "Annual / Seasonal Rainfall (mm)", font: { family: "'Inter', sans-serif" } },
          grid: { color: "#F1F5F9" }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderPhase3MonsoonRankings(rankings) {
  const tbody = document.getElementById("monsoonRankTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (rankings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--color-text-muted); padding: 14px;">No matching districts.</td></tr>`;
    return;
  }

  rankings.forEach(d => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="font-family: var(--font-mono); font-weight: 700; color: var(--color-primary);">${d.rank || "--"}</td>
      <td><strong>${d.district_name}</strong> <span style="font-size: 0.72rem; color: var(--color-text-muted);">(${d.tamil_name})</span></td>
      <td>${d.zone}</td>
      <td style="font-family: var(--font-mono); font-weight: 700;">${d.recorded_mm} mm</td>
      <td style="font-family: var(--font-mono); color: var(--color-text-secondary);">${d.normal_mm} mm</td>
      <td style="font-family: var(--font-mono); font-weight: 700; color: ${d.departure_pct >= 0 ? 'var(--color-forest)' : 'var(--color-critical)'};">${d.departure_pct > 0 ? '+' : ''}${d.departure_pct}%</td>
      <td><span class="badge-saas ${getRiskBadgeClass(d.imd_category)}">${d.imd_category}</span></td>
      <td style="text-align: right;"><button class="btn-saas btn-saas-secondary btn-saas-sm select-from-rank-btn" data-district="${d.district_id}">View</button></td>
    `;

    tr.querySelector(".select-from-rank-btn").addEventListener("click", () => {
      selectDistrict(d.district_id);
      document.getElementById("overview")?.scrollIntoView({ behavior: "smooth" });
    });

    tbody.appendChild(tr);
  });
}

// 14.3 Climate Anomalies Matrix & Heatmap
async function fetchPhase3Anomalies(districtId) {
  try {
    const res = await fetch(`${API_BASE}/api/climate/anomalies?district=${districtId}&start_year=2015&end_year=2024`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const neutralEl = document.getElementById("badgeAnomNeutral");
    const warnEl = document.getElementById("badgeAnomWarning");
    const critEl = document.getElementById("badgeAnomCritical");

    if (neutralEl) neutralEl.textContent = `Neutral: ${data.severity_summary.neutral}`;
    if (warnEl) warnEl.textContent = `Warning: ${data.severity_summary.warning}`;
    if (critEl) critEl.textContent = `High-Risk: ${data.severity_summary.high_risk}`;

    renderPhase3AnomalyMatrix(data.matrix_heatmap || []);
  } catch (err) {
    console.error("Phase 3 anomalies fetch error:", err);
  }
}

function renderPhase3AnomalyMatrix(matrixCells) {
  const tbody = document.getElementById("anomalyMatrixTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  // Group by year (2015..2024)
  const yearsMap = {};
  matrixCells.forEach(c => {
    if (!yearsMap[c.year]) yearsMap[c.year] = {};
    yearsMap[c.year][c.month_num] = c;
  });

  const sortedYears = Object.keys(yearsMap).map(Number).sort((a, b) => b - a);
  sortedYears.forEach(yr => {
    const tr = document.createElement("tr");
    let rowHtml = `<td style="font-weight: 700; background-color: var(--color-surface-muted);">${yr}</td>`;

    for (let m = 1; m <= 12; m++) {
      const cell = yearsMap[yr][m];
      if (cell) {
        let cls = "cell-anom-neutral";
        if (cell.severity === "High-Risk") cls = "cell-anom-critical";
        else if (cell.severity === "Warning") cls = "cell-anom-warning";

        const title = `${cell.month_name} ${yr}: Temp Anom: ${cell.temp_anomaly_celsius > 0 ? '+' : ''}${cell.temp_anomaly_celsius}°C | Rain: ${cell.actual_rain_mm}mm (${cell.rainfall_departure_pct > 0 ? '+' : ''}${cell.rainfall_departure_pct}%) | Status: ${cell.severity}`;
        rowHtml += `<td class="${cls}" title="${title}">${cell.temp_anomaly_celsius > 0 ? '+' : ''}${cell.temp_anomaly_celsius.toFixed(1)}°</td>`;
      } else {
        rowHtml += `<td>--</td>`;
      }
    }

    tr.innerHTML = rowHtml;
    tbody.appendChild(tr);
  });
}

// 14.4 Report Generator Form
function setupPhase3ReportGenerator() {
  const districtSelect = document.getElementById("reportDistrictSelect");
  if (districtSelect && allDistricts.length > 0 && districtSelect.children.length === 0) {
    allDistricts.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d.id;
      opt.textContent = `${d.name} (${d.region})`;
      if (d.id === currentDistrictId) opt.selected = true;
      districtSelect.appendChild(opt);
    });
  }

  const generateBtn = document.getElementById("generateReportBtn");
  if (generateBtn) {
    generateBtn.addEventListener("click", async () => {
      const dist = document.getElementById("reportDistrictSelect")?.value || currentDistrictId;
      const startYr = parseInt(document.getElementById("reportStartYear")?.value || "2015", 10);
      const endYr = parseInt(document.getElementById("reportEndYear")?.value || "2024", 10);
      const season = document.getElementById("reportSeasonSelect")?.value || "all";
      const variable = document.getElementById("reportVariableSelect")?.value || "all";
      const format = document.getElementById("reportFormatSelect")?.value || "both";

      const btnText = document.getElementById("generateReportBtnText");
      if (btnText) btnText.textContent = "Compiling & Generating Official Dossier...";
      generateBtn.disabled = true;

      try {
        const res = await fetch(`${API_BASE}/api/climate/reports`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            district: dist,
            start_year: startYr,
            end_year: endYr,
            season: season,
            variable: variable,
            format: format
          })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const report = await res.json();

        // Update result card
        const resultCard = document.getElementById("reportResultCard");
        const titleEl = document.getElementById("resultReportTitle");
        const metaEl = document.getElementById("resultReportMeta");
        const pdfLink = document.getElementById("downloadPdfLink");
        const csvLink = document.getElementById("downloadCsvLink");

        if (titleEl) titleEl.textContent = report.title;
        if (metaEl) metaEl.textContent = `Report ID: ${report.report_id} · Generated: ${new Date(report.created_at).toLocaleTimeString()} IST · Baseline: IMD 1991–2020`;
        if (pdfLink) pdfLink.href = `${API_BASE}${report.pdf_url}`;
        if (csvLink) csvLink.href = `${API_BASE}${report.csv_url}`;

        if (resultCard) {
          resultCard.style.display = "block";
          resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        showToast(`Official Climate Report (${report.report_id}) created!`, "success");
      } catch (err) {
        console.error("Report generation error:", err);
        showToast("Error generating climate report.", "critical");
      } finally {
        if (btnText) btnText.textContent = "Generate & Download Official Dossier";
        generateBtn.disabled = false;
      }
    });
  }
}

// ==============================================================================
// 15. Phase 4 — AI Models & Leakage-Free Forecast Evaluation Engine
// ==============================================================================
function initPhase4MLEvaluation() {
  const horizonSelect = document.getElementById("mlHorizonSelect");
  if (horizonSelect) {
    horizonSelect.addEventListener("change", () => {
      loadPhase4MLEvaluation(currentDistrictId);
    });
  }

  const runBacktestBtn = document.getElementById("btnRunBacktest");
  if (runBacktestBtn) {
    runBacktestBtn.addEventListener("click", async () => {
      const horizon = parseInt(document.getElementById("mlHorizonSelect")?.value || "24", 10);
      runBacktestBtn.disabled = true;
      runBacktestBtn.innerHTML = `<svg class="spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;margin-right:4px;"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg> Rolling Backtest Running...`;

      try {
        const res = await fetch(`${API_BASE}/api/ml/run-backtest`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ horizon_hours: horizon })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const manifest = await res.json();
        showToast(`Rolling-Origin Backtest (${manifest.experiment_id}) verified with 0 leakage!`, "success");
        await loadPhase4MLEvaluation(currentDistrictId);
      } catch (err) {
        console.error("Backtest execution error:", err);
        showToast("Error executing rolling-origin backtest.", "critical");
      } finally {
        runBacktestBtn.disabled = false;
        runBacktestBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px;"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Run Rolling Backtest`;
      }
    });
  }

  // Load initial Phase 4 suite
  loadPhase4MLEvaluation(currentDistrictId);
}

async function loadPhase4MLEvaluation(districtId) {
  const horizon = parseInt(document.getElementById("mlHorizonSelect")?.value || "24", 10);
  await Promise.all([
    fetchPhase4LiveForecast(districtId, horizon),
    fetchPhase4Leaderboard(horizon),
    fetchPhase4BacktestChart(districtId),
    fetchPhase4TimesFMComp()
  ]);
}

// 15.1 Live ML Forecast vs NWP
async function fetchPhase4LiveForecast(districtId, horizon = 24) {
  try {
    const res = await fetch(`${API_BASE}/api/ml/forecast?district=${districtId}&horizon=${horizon}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const f = await res.json();

    const tempEl = document.getElementById("mlPredTemp");
    const ciEl = document.getElementById("mlTempCI");
    const rainProbEl = document.getElementById("mlPredRainProb");
    const rainMmEl = document.getElementById("mlPredRainMm");
    const issueTimeEl = document.getElementById("mlIssueTime");
    const modelTitleEl = document.getElementById("mlModelTitle");

    if (tempEl) tempEl.textContent = `${f.predicted_temperature_c} °C`;
    if (ciEl && f.temperature_80_ci) ciEl.textContent = `[80% CI: ${f.temperature_80_ci[0]}° to ${f.temperature_80_ci[1]}°]`;
    if (rainProbEl) rainProbEl.textContent = `${f.rain_probability_pct}%`;
    if (rainMmEl) rainMmEl.textContent = `${f.predicted_rainfall_mm} mm (${f.rainfall_condition})`;
    if (issueTimeEl) issueTimeEl.textContent = `Issue: ${new Date(f.forecast_issue_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} IST`;
    if (modelTitleEl) modelTitleEl.textContent = `LightGBM ${f.district_name} (${f.horizon_hours}h Forecaster)`;
  } catch (err) {
    console.error("Live ML forecast load error:", err);
  }
}

// 15.2 Leaderboard Table & Seasonal Metrics
async function fetchPhase4Leaderboard(horizon = 24) {
  try {
    const res = await fetch(`${API_BASE}/api/ml/experiments`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const exp = await res.json();

    renderPhase4Leaderboard(exp.test_leaderboard, exp.best_model);

    // Update Seasonal Breakdown cards
    const sb = exp.seasonal_breakdown || {};
    const nem = sb["NEM (Northeast Monsoon: Oct-Dec)"];
    const swm = sb["SWM (Southwest Monsoon: Jun-Sep)"];

    if (nem) {
      const el = document.getElementById("nemTempMae"); if (el) el.textContent = `${nem.temp_mae} °C`;
      const elR = document.getElementById("nemRainMae"); if (elR) elR.textContent = `${nem.rain_mae} mm`;
      const elW = document.getElementById("nemWetMae"); if (elW) elW.textContent = `${nem.wet_day_mae} mm`;
      const elF = document.getElementById("nemRainF1"); if (elF) elF.textContent = `${nem.rain_f1}`;
    }

    if (swm) {
      const el = document.getElementById("swmTempMae"); if (el) el.textContent = `${swm.temp_mae} °C`;
      const elR = document.getElementById("swmRainMae"); if (elR) elR.textContent = `${swm.rain_mae} mm`;
      const elW = document.getElementById("swmWetMae"); if (elW) elW.textContent = `${swm.wet_day_mae} mm`;
      const elF = document.getElementById("swmRainF1"); if (elF) elF.textContent = `${swm.rain_f1}`;
    }

    // Update Heavy Rain Metrics
    const championMet = exp.test_leaderboard?.lightgbm;
    if (championMet && championMet.heavy_rain_event) {
      const hr = championMet.heavy_rain_event;
      const elRec = document.getElementById("heavyRecall"); if (elRec) elRec.textContent = `${(hr.event_recall * 100).toFixed(1)}%`;
      const elPrec = document.getElementById("heavyPrecision"); if (elPrec) elPrec.textContent = `${(hr.event_precision * 100).toFixed(1)}%`;
      const elFar = document.getElementById("heavyFar"); if (elFar) elFar.textContent = `${(hr.false_alarm_rate * 100).toFixed(1)}%`;
    }
  } catch (err) {
    console.error("Leaderboard load error:", err);
  }
}

function renderPhase4Leaderboard(board, bestModelName = "lightgbm") {
  const tbody = document.getElementById("mlLeaderboardBody");
  if (!tbody || !board) return;
  tbody.innerHTML = "";

  const modelMeta = {
    persistence: { name: "Persistence Baseline", category: "Heuristic (t-1)", status: "Baseline Reference" },
    seasonal_naive: { name: "Seasonal Naive", category: "Cyclical (Lag-3d)", status: "Baseline Reference" },
    ridge: { name: "Ridge Regression", category: "Linear L2 Regularized", status: "Interpretable ML" },
    lightgbm: { name: "LightGBM HistGBDT", category: "Nonlinear Ensemble", status: "Selected Champion" },
    timesfm: { name: "Hugging Face TimesFM (200M)", category: "Zero-Shot Foundation", status: "Benchmarked Adapter" }
  };

  const order = ["lightgbm", "ridge", "timesfm", "persistence", "seasonal_naive"];

  order.forEach(mKey => {
    const m = board[mKey];
    if (!m) return;
    const meta = modelMeta[mKey] || { name: mKey, category: "Model", status: "Evaluated" };
    const isChampion = mKey === bestModelName;

    const tr = document.createElement("tr");
    if (isChampion) tr.style.backgroundColor = "rgba(27, 138, 90, 0.04)";

    tr.innerHTML = `
      <td>
        <strong style="color: ${isChampion ? 'var(--color-forest)' : 'var(--color-text-primary)'};">${meta.name}</strong>
      </td>
      <td><span style="font-size: 0.75rem; color: var(--color-text-secondary);">${meta.category}</span></td>
      <td><strong>${m.temperature.mae} °C</strong></td>
      <td><span style="color: var(--color-text-secondary);">${m.temperature.rmse} °C</span></td>
      <td><strong>${m.rainfall.mae} mm</strong></td>
      <td><span>${m.rainfall.wet_day_mae} mm</span></td>
      <td><strong style="color: ${m.rain_classification.f1_score >= 0.6 ? 'var(--color-forest)' : 'var(--color-text-primary)'};">${m.rain_classification.f1_score}</strong></td>
      <td><span style="color: ${m.heavy_rain_event?.false_alarm_rate > 0.8 ? 'var(--color-danger)' : 'var(--color-text-secondary)'};">${((m.heavy_rain_event?.false_alarm_rate || 0) * 100).toFixed(1)}%</span></td>
      <td>${m.latency_ms} ms</td>
      <td>${m.memory_mb} MB</td>
      <td>
        <span class="badge-saas ${isChampion ? 'badge-normal' : (mKey === 'timesfm' ? 'badge-warning' : 'badge-neutral')}" style="${isChampion ? 'background-color: rgba(27,138,90,0.12); color: var(--color-forest); font-weight:700;' : ''}">
          ${meta.status}
        </span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// 15.3 Rolling-Origin Backtest Chart
async function fetchPhase4BacktestChart(districtId) {
  try {
    const res = await fetch(`${API_BASE}/api/ml/backtest-results?district=${districtId}&limit=35`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderPhase4BacktestChart(data);
  } catch (err) {
    console.error("Backtest chart load error:", err);
  }
}

function renderPhase4BacktestChart(data) {
  const ctx = document.getElementById("backtestChart");
  if (!ctx || !data.timestamps) return;
  if (backtestChartInstance) backtestChartInstance.destroy();

  const labels = data.timestamps;
  const actualTemps = data.temperature.actual;
  const predTemps = data.temperature.predicted;
  const upper80 = data.temperature.upper_80_ci;
  const lower80 = data.temperature.lower_80_ci;

  backtestChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Observed Actual Temperature",
          data: actualTemps,
          borderColor: "#0f3b4c",
          backgroundColor: "#0f3b4c",
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: "#0f3b4c",
          tension: 0.2,
          order: 1
        },
        {
          label: "LightGBM Walk-Forward Forecast",
          data: predTemps,
          borderColor: "#1b8a5a",
          borderDash: [5, 4],
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: "#1b8a5a",
          tension: 0.2,
          order: 2
        },
        {
          label: "80% Confidence Bound Upper",
          data: upper80,
          borderColor: "rgba(27, 138, 90, 0.25)",
          borderWidth: 1,
          pointRadius: 0,
          fill: "+1",
          backgroundColor: "rgba(27, 138, 90, 0.08)",
          tension: 0.2,
          order: 3
        },
        {
          label: "80% Confidence Bound Lower",
          data: lower80,
          borderColor: "rgba(27, 138, 90, 0.25)",
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
          tension: 0.2,
          order: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "top",
          labels: {
            font: { family: "Inter", size: 11, weight: 600 },
            filter: item => !item.text.includes("Confidence Bound Lower")
          }
        },
        tooltip: {
          callbacks: {
            label: context => `${context.dataset.label}: ${context.parsed.y} °C`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: "Inter", size: 10 } }
        },
        y: {
          title: { display: true, text: "Temperature (°C)", font: { family: "Inter", size: 11 } },
          grid: { color: "rgba(0,0,0,0.05)" },
          ticks: { font: { family: "Inter", size: 10 } }
        }
      }
    }
  });
}

// 15.4 TimesFM Operational Benchmark Comparison
async function fetchPhase4TimesFMComp() {
  try {
    const res = await fetch(`${API_BASE}/api/ml/timesfm-benchmark`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const dossier = await res.json();
    renderPhase4TimesFMComp(dossier);
  } catch (err) {
    console.error("TimesFM benchmark load error:", err);
  }
}

function renderPhase4TimesFMComp(dossier) {
  const tbody = document.getElementById("timesfmCompBody");
  if (!tbody || !dossier.operational_comparison) return;
  tbody.innerHTML = "";

  dossier.operational_comparison.forEach(item => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${item.dimension}</strong></td>
      <td style="color: var(--color-text-secondary);">${item.timesfm}</td>
      <td style="color: var(--color-forest); font-weight: 700;">${item.lightgbm_inhouse}</td>
      <td><span style="font-size: 0.78rem; color: var(--color-text-primary);">${item.advantage}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// ==============================================================================
// 16. Phase 5 — Meteorological Risk Intelligence & Early Warning Hub
// ==============================================================================
let currentRiskLanguage = "en";
let cachedBilingualSummary = null;
let currentAlertStatusFilter = "Active";
let cachedDistrictRisks = [];
let cachedAlertsHistory = [];

function initPhase5RiskIntelligence() {
  // 16.1 Language Toggle Buttons (English / Tamil)
  const btnEn = document.getElementById("btnLangEn");
  const btnTa = document.getElementById("btnLangTa");

  if (btnEn && btnTa) {
    btnEn.addEventListener("click", () => {
      btnEn.classList.add("active");
      btnTa.classList.remove("active");
      currentRiskLanguage = "en";
      renderBilingualSummary();
    });

    btnTa.addEventListener("click", () => {
      btnTa.classList.add("active");
      btnEn.classList.remove("active");
      currentRiskLanguage = "ta";
      renderBilingualSummary();
    });
  }

  // 16.2 Risk Radar Severity Filter & Search
  const sevFilter = document.getElementById("riskSeverityFilter");
  if (sevFilter) {
    sevFilter.addEventListener("change", () => filterAndRenderRiskTable());
  }

  const searchInput = document.getElementById("riskTableSearch");
  if (searchInput) {
    searchInput.addEventListener("input", () => filterAndRenderRiskTable());
  }

  // 16.3 Alert History Status Tabs (Active / Updated / Resolved)
  const statusTabs = document.querySelectorAll("[data-alert-status]");
  statusTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      statusTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentAlertStatusFilter = tab.getAttribute("data-alert-status") || "Active";
      fetchPhase5AlertsHistory();
    });
  });

  // Initial Load of Phase 5 Suite
  fetchPhase5RiskOverview();
  fetchPhase5DistrictsRisk();
  fetchPhase5AlertsHistory();
  loadPhase5RiskData(currentDistrictId);
}

// Load district-specific bilingual summary
async function loadPhase5RiskData(districtId) {
  try {
    const res = await fetch(`${API_BASE}/api/risk/summaries/${districtId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    cachedBilingualSummary = await res.json();
    renderBilingualSummary();
  } catch (err) {
    console.error("Phase 5 bilingual summary error:", err);
    const box = document.getElementById("bilingualContentArea");
    if (box) {
      box.innerHTML = `<div style="font-size: 0.85rem; color: var(--color-text-muted); padding: 12px 0;">Risk telemetry evaluating for ${districtId}...</div>`;
    }
  }
}

function renderBilingualSummary() {
  const container = document.getElementById("bilingualContentArea");
  const badge = document.getElementById("bilingualDistBadge");
  if (!container || !cachedBilingualSummary) return;

  const data = cachedBilingualSummary;
  const isTa = currentRiskLanguage === "ta";
  const langKey = isTa ? "ta" : "en";

  const distName = typeof data.district_name === "object"
    ? (data.district_name[langKey] || data.district_name.en)
    : (data.district_name || currentDistrictId.toUpperCase());

  const compSev = typeof data.composite_severity === "object"
    ? (data.composite_severity[langKey] || data.composite_severity.en)
    : (data.composite_severity || "Low");

  if (badge) {
    badge.textContent = isTa
      ? `${distName} மாவட்டம் (${compSev} அபாயம்)`
      : `${distName} District (${compSev} Risk)`;
  }

  const hazards = data.bilingual_hazards || [];
  let compoundRiskHtml = "";
  if (data.compound_risk && data.compound_risk.detected) {
    compoundRiskHtml = `
      <div style="background-color: #fef2f2; border: 1px solid #fecaca; border-radius: var(--radius-sm); padding: 10px 14px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-critical);"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <span style="font-size: 0.82rem; color: #991b1b; font-weight: 600;">
          ${isTa ? 'கூட்டு ஆபத்து கண்டறியப்பட்டது: ' : 'Compound Risk Alert: '}
          ${data.compound_risk.description}
        </span>
      </div>
    `;
  }

  let hazardsHtml = hazards.map(h => {
    const hName = h.hazard_name ? (h.hazard_name[langKey] || h.hazard_name.en) : h.hazard_type;
    const hSev = h.severity ? (h.severity[langKey] || h.severity.en) : "Low";
    const badgeClass = getRiskSeverityBadgeClass(h.severity ? h.severity.en : "Low");
    const summaryObj = h.summary ? (h.summary[langKey] || h.summary.en) : {};
    const headline = summaryObj.headline || `${hSev} ${hName}`;
    const desc = summaryObj.description || "";
    const prec = summaryObj.precautions || "Observe standard advisories.";

    return `
      <div class="bilingual-brief-box" style="margin-bottom: 12px;">
        <div class="bilingual-header-line">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="badge-saas ${badgeClass}">${hName} &bull; ${hSev}</span>
            <span style="font-size: 0.78rem; font-weight: 600; color: var(--color-text-secondary);">${h.forecast_period || "Next 24 Hours"}</span>
          </div>
          <span style="font-size: 0.72rem; color: var(--color-text-muted); font-family: var(--font-mono);">
            Trigger: <strong>${h.trigger_value} ${h.unit}</strong> (Threshold: ${h.threshold_value} ${h.unit})
          </span>
        </div>

        <div class="bilingual-prose">
          <strong style="color: var(--color-text-primary);">${headline}</strong>
          <div style="margin-top: 4px;">${desc}</div>
        </div>

        <div class="bilingual-precautions">
          <strong>${isTa ? 'முன்னெச்சரிக்கை வழிகாட்டுதல்:' : 'Precautions & Recommended Action:'}</strong>
          <div>${prec}</div>
        </div>
      </div>
    `;
  }).join("");

  container.innerHTML = `
    ${compoundRiskHtml}
    ${hazardsHtml}
    <div style="font-size: 0.74rem; color: var(--color-text-muted); border-top: 1px dashed var(--color-border); padding-top: 8px; margin-top: 8px;">
      <em>${data.disclaimer || (isTa
        ? "விண்ணப்பத்தால் கணக்கிடப்பட்ட இடர் மதிப்பீடுகள் உள்ளூர் வரம்புகளின் அடிப்படையில் உருவாக்கப்பட்டவை. இவை இந்திய வானிலை மையத்தின் (IMD) அதிகாரப்பூர்வ எச்சரிக்கைகளுக்கு மாற்றாகாது."
        : "Application-calculated risk ratings are based on automated local thresholds and do not replace official warnings issued by the India Meteorological Department (IMD)."
      )}</em>
    </div>
  `;
}

// Fetch statewide overview KPIs
async function fetchPhase5RiskOverview() {
  try {
    const res = await fetch(`${API_BASE}/api/risk/overview`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const activeEl = document.getElementById("riskActiveAlertsCount");
    const highEl = document.getElementById("riskHighRiskCount");
    const resolvedEl = document.getElementById("riskResolvedCount");
    const imdStatusPill = document.getElementById("imdStatusPill");
    const imdStatusSub = document.getElementById("imdStatusSub");

    if (activeEl) activeEl.textContent = data.active_alerts_count ?? 0;
    if (highEl) highEl.textContent = (data.high_risk_hotspots ? data.high_risk_hotspots.length : 0);
    if (resolvedEl) resolvedEl.textContent = data.resolved_alerts_count ?? 0;

    if (imdStatusPill) {
      imdStatusPill.textContent = "Active Regional Watch";
    }
    if (imdStatusSub) {
      imdStatusSub.textContent = "IMD RMC Chennai Official Link";
    }
  } catch (err) {
    console.error("Phase 5 risk overview error:", err);
  }
}

// Fetch 38-district risk radar
async function fetchPhase5DistrictsRisk() {
  try {
    const res = await fetch(`${API_BASE}/api/risk/districts`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    cachedDistrictRisks = await res.json();
    filterAndRenderRiskTable();
  } catch (err) {
    console.error("Phase 5 districts risk error:", err);
  }
}

function filterAndRenderRiskTable() {
  const tbody = document.getElementById("riskTableBody");
  if (!tbody) return;

  const sevFilter = document.getElementById("riskSeverityFilter")?.value || "all";
  const searchQ = (document.getElementById("riskTableSearch")?.value || "").toLowerCase().trim();

  const filtered = cachedDistrictRisks.filter(d => {
    // Severity filter match
    if (sevFilter !== "all" && d.composite_risk !== sevFilter) {
      return false;
    }
    // Search text match
    if (searchQ) {
      const matchName = (d.district_name || "").toLowerCase().includes(searchQ);
      const matchTa = (d.tamil_name || "").toLowerCase().includes(searchQ);
      const matchZone = (d.zone || "").toLowerCase().includes(searchQ);
      if (!matchName && !matchTa && !matchZone) return false;
    }
    return true;
  });

  tbody.innerHTML = "";
  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--color-text-muted); padding: 16px;">No districts match the selected filters.</td></tr>`;
    return;
  }

  filtered.forEach(r => {
    const tr = document.createElement("tr");
    const badgeClass = getRiskSeverityBadgeClass(r.composite_risk);

    tr.innerHTML = `
      <td><strong>${r.district_name}</strong> <span style="font-size: 0.74rem; color: var(--color-text-muted);">(${r.tamil_name || ''})</span></td>
      <td>${r.zone || 'Tamil Nadu'}</td>
      <td><span class="badge-saas ${badgeClass}">${r.composite_risk}</span></td>
      <td>${formatHazardAlert(r.alerts?.heavy_rain)}</td>
      <td>${formatHazardAlert(r.alerts?.heat_stress)}</td>
      <td>${formatHazardAlert(r.alerts?.high_wind)}</td>
      <td>${formatHazardAlert(r.alerts?.dry_spell)}</td>
      <td>
        <button class="btn-saas btn-saas-secondary btn-saas-sm select-risk-district-btn" data-district="${r.district_id}">
          Inspect
        </button>
      </td>
    `;

    tr.querySelector(".select-risk-district-btn").addEventListener("click", () => {
      selectDistrict(r.district_id);
      document.getElementById("heatrisk")?.scrollIntoView({ behavior: "smooth" });
    });

    tbody.appendChild(tr);
  });
}

function formatHazardAlert(val) {
  if (!val || val === "None" || val === "Low") {
    return `<span style="color: var(--color-text-muted); font-size: 0.8rem;">Low / None</span>`;
  }
  const badgeClass = getRiskSeverityBadgeClass(val);
  return `<span class="badge-saas ${badgeClass}" style="font-size: 0.7rem;">${val}</span>`;
}

function getRiskSeverityBadgeClass(severity) {
  if (!severity || typeof severity !== "string") return "badge-low";
  const s = severity.toLowerCase();
  if (s.includes("severe") || s.includes("danger") || s.includes("critical")) return "badge-severe";
  if (s.includes("high") || s.includes("warning")) return "badge-high";
  if (s.includes("moderate") || s.includes("advisory")) return "badge-moderate";
  return "badge-low";
}

// Fetch SQLite persistent alert history
async function fetchPhase5AlertsHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/risk/alerts?status=${currentAlertStatusFilter}&limit=50`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    cachedAlertsHistory = await res.json();
    renderAlertsHistoryTable(cachedAlertsHistory);
  } catch (err) {
    console.error("Phase 5 alert history load error:", err);
  }
}

function renderAlertsHistoryTable(alerts) {
  const tbody = document.getElementById("alertsHistoryBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (!alerts || alerts.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--color-text-muted); padding: 18px;">No ${currentAlertStatusFilter} alerts recorded in persistent SQLite audit log.</td></tr>`;
    return;
  }

  alerts.forEach(a => {
    const tr = document.createElement("tr");
    const badgeClass = getRiskSeverityBadgeClass(a.severity);
    const dateFormatted = a.updated_at ? new Date(a.updated_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : '--';

    tr.innerHTML = `
      <td><span class="font-mono" style="font-size: 0.75rem; font-weight: 600;">${a.alert_id}</span></td>
      <td><strong>${a.district_id.toUpperCase()}</strong></td>
      <td>${a.hazard_type}</td>
      <td><span class="badge-saas ${badgeClass}">${a.severity}</span></td>
      <td><span class="font-mono" style="font-size: 0.75rem;">${a.trigger_value} / ${a.threshold_value} ${a.unit}</span></td>
      <td style="max-width: 220px; font-size: 0.76rem; color: var(--color-text-secondary);">${a.reason}</td>
      <td><span class="badge-saas ${a.status === 'Active' ? 'badge-critical' : (a.status === 'Updated' ? 'badge-advisory' : 'badge-normal')}">${a.status}</span></td>
      <td>
        <span style="font-size: 0.75rem; color: ${a.is_acknowledged ? 'var(--color-forest)' : 'var(--color-warning)'}; font-weight: 600;">
          ${a.is_acknowledged ? 'Yes (' + (a.acknowledged_by || 'Staff') + ')' : 'Pending'}
        </span>
      </td>
      <td style="font-size: 0.72rem; color: var(--color-text-muted);">${dateFormatted}</td>
      <td>
        ${!a.is_acknowledged && a.status !== 'Resolved'
          ? `<button class="btn-ack" data-ack-id="${a.alert_id}">Acknowledge</button>`
          : `<span style="font-size: 0.72rem; color: var(--color-text-muted);">&mdash;</span>`
        }
      </td>
    `;

    const ackBtn = tr.querySelector("[data-ack-id]");
    if (ackBtn) {
      ackBtn.addEventListener("click", () => acknowledgeAlertHandler(a.alert_id));
    }

    tbody.appendChild(tr);
  });
}

async function acknowledgeAlertHandler(alertId) {
  try {
    const res = await fetch(`${API_BASE}/api/risk/alerts/${alertId}`, {
      method: "PATCH"
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    showToast(`Alert ${alertId} acknowledged and audited in SQLite.`, "success");
    await fetchPhase5AlertsHistory();
    await fetchPhase5RiskOverview();
  } catch (err) {
    console.error("Alert acknowledgment error:", err);
    showToast("Failed to acknowledge alert.", "critical");
  }
}

// ==============================================================================
// OPERATIONAL INTELLIGENCE CONTROLLER (MODULES 1, 2, 3)
// ==============================================================================

let currentGuidanceHorizon = 24;
let currentSectorFilter = "all";
let currentSectorHorizon = 24;
let currentSectorSort = "severity_desc";
let cachedGuidanceData = null;
let cachedSectorMatrixData = null;

function initOperationalIntelligence() {
  setupOperationalGuidanceControls();
  setupSectorMatrixControls();
  setupSettingsAndSourcesControls();

  fetchComputedGuidance(currentDistrictId, currentGuidanceHorizon);
  fetchSectorMatrix(currentDistrictId, currentSectorFilter, currentSectorHorizon, currentSectorSort);
  fetchDataSourcesRegistry();
  fetchOperationalConfig();
  fetchOperationalAuditLog();
}

function setupOperationalGuidanceControls() {
  const horizonBtns = document.querySelectorAll("[data-guidance-horizon]");
  horizonBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      horizonBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentGuidanceHorizon = parseInt(btn.getAttribute("data-guidance-horizon"), 10);
      fetchComputedGuidance(currentDistrictId, currentGuidanceHorizon);
    });
  });
}

async function fetchComputedGuidance(districtId, horizon = 24) {
  try {
    const res = await fetch(`${API_BASE}/api/guidance/${districtId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    cachedGuidanceData = data;
    renderComputedGuidance(data, horizon);
  } catch (err) {
    console.error("Error fetching computed guidance:", err);
  }
}

function renderComputedGuidance(data, horizon) {
  if (!data) return;

  const therm = data.thermal_conditions || {};
  const precip = data.precipitation || {};
  const flow = data.atmospheric_flow || {};
  const state = data.atmospheric_state || {};
  const trace = data.traceability || {};

  // Traceability & timestamps
  const updateEl = document.getElementById("guidanceUpdateTime");
  if (updateEl && trace.last_updated_utc) {
    updateEl.textContent = new Date(trace.last_updated_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " UTC";
  }

  // Panel 1: Thermal Conditions
  const gTemp = document.getElementById("guidanceTemp");
  const gAppTemp = document.getElementById("guidanceApparentTemp");
  const gHeatIndex = document.getElementById("guidanceHeatIndex");
  const gDiurnal = document.getElementById("guidanceDiurnalRange");
  const gTempRange = document.getElementById("guidanceTempRange");
  const gTempAno = document.getElementById("guidanceTempAnomaly");
  const gThermText = document.getElementById("thermalGuidanceText");
  const gThermBadge = document.getElementById("thermalExposureBadge");

  if (gTemp) gTemp.textContent = therm.temperature_c ?? "--";
  if (gAppTemp) gAppTemp.textContent = `${therm.apparent_temperature_c ?? "--"} °C`;
  if (gHeatIndex) gHeatIndex.textContent = `${therm.heat_index_c ?? "--"} °C`;
  if (gDiurnal) gDiurnal.textContent = `${therm.diurnal_range_c ?? "--"} °C`;
  if (gTempRange) gTempRange.textContent = `${therm.max_forecast_temp_c ?? "--"} / ${therm.min_forecast_temp_c ?? "--"} °C`;
  if (gTempAno) {
    const diff = (therm.temperature_c ?? 30) - 30.0;
    const sign = diff >= 0 ? "+" : "";
    gTempAno.textContent = `${sign}${diff.toFixed(1)} °C vs Baseline`;
  }
  if (gThermText) gThermText.textContent = therm.guidance || "Benign thermal conditions; standard outdoor comfort.";
  if (gThermBadge) {
    gThermBadge.textContent = therm.heat_category || "Moderate";
    gThermBadge.className = `badge-saas ${therm.heat_category === 'Severe' ? 'badge-critical' : (therm.heat_category === 'High' ? 'badge-advisory' : 'badge-normal')}`;
  }

  // Panel 2: Precipitation
  const gPrecip24 = document.getElementById("guidancePrecip24h");
  const gRainProb = document.getElementById("guidanceRainProb");
  const gRainInt = document.getElementById("guidanceRainIntensity");
  const gAccums = document.getElementById("guidanceAccumulations");
  const gPrecipDep = document.getElementById("guidancePrecipDeparture");
  const gDrySpell = document.getElementById("guidanceDrySpell");
  const gPrecipText = document.getElementById("precipGuidanceText");
  const gPrecipBadge = document.getElementById("precipIntensityBadge");

  if (gPrecip24) gPrecip24.textContent = precip.accumulation_24h_mm ?? "0.0";
  if (gRainProb) gRainProb.textContent = `${precip.probability_pct ?? 25}%`;
  if (gRainInt) gRainInt.textContent = precip.intensity_classification || "Dry / Negligible";
  if (gAccums) gAccums.textContent = `${precip.accumulation_6h_mm ?? 0} / ${precip.accumulation_48h_mm ?? 0} / ${precip.accumulation_72h_mm ?? 0} mm`;
  if (gPrecipDep && precip.rainfall_anomaly) {
    const dep = precip.rainfall_anomaly.departure_pct ?? 0;
    const sign = dep >= 0 ? "+" : "";
    gPrecipDep.textContent = `${sign}${dep}% (${precip.rainfall_anomaly.departure_category || 'Normal'})`;
  }
  const dryMetrics = data.dry_spell_metrics || {};
  if (gDrySpell) gDrySpell.textContent = `${dryMetrics.consecutive_dry_days ?? 0} Consecutive Days`;
  if (gPrecipText) {
    const r24 = precip.accumulation_24h_mm ?? 0;
    gPrecipText.textContent = r24 >= 64.5
      ? "Heavy precipitation accumulation; monitor drainage chokepoints and urban subways."
      : (r24 >= 15.6 ? "Moderate convective showers; standard agricultural field drainage applies." : "Dry / light showers; negligible operational constraint.");
  }
  if (gPrecipBadge) {
    const cat = precip.intensity_classification || "Dry";
    gPrecipBadge.textContent = cat;
    gPrecipBadge.className = `badge-saas ${cat.includes('Heavy') ? 'badge-critical' : (cat.includes('Moderate') ? 'badge-advisory' : 'badge-normal')}`;
  }

  // Panel 3: Atmospheric Flow
  const gWindSpeed = document.getElementById("guidanceWindSpeed");
  const gWindGusts = document.getElementById("guidanceWindGusts");
  const gWindDir = document.getElementById("guidanceWindDir");
  const gCoastExp = document.getElementById("guidanceCoastalExposure");
  const gSquall = document.getElementById("guidanceSquallRisk");
  const gTransHaz = document.getElementById("guidanceTransportHazard");
  const gWindText = document.getElementById("windGuidanceText");
  const gWindBadge = document.getElementById("windExposureBadge");

  if (gWindSpeed) gWindSpeed.textContent = flow.wind_speed_kmh ?? "--";
  if (gWindGusts) gWindGusts.textContent = `${flow.wind_gusts_kmh ?? "--"} km/h`;
  if (gWindDir) gWindDir.textContent = `${flow.wind_direction_deg ?? 0}° (${flow.wind_compass || 'ENE'})`;
  if (gCoastExp) gCoastExp.textContent = data.is_coastal ? "Coastal Exposed Zone" : "Inland Low Exposure";
  if (gSquall) gSquall.textContent = (flow.wind_gusts_kmh ?? 0) >= 45.0 ? "Elevated Gale Risk" : "Nominal (<45 km/h)";
  if (gTransHaz) gTransHaz.textContent = (flow.wind_speed_kmh ?? 0) >= 40.0 ? "High Wind Caution" : "Nominal";
  if (gWindText) gWindText.textContent = flow.guidance || "Light to moderate breeze; negligible operational constraint.";
  if (gWindBadge) {
    gWindBadge.textContent = flow.exposure_level || "Low";
    gWindBadge.className = `badge-saas ${flow.exposure_level === 'Severe' ? 'badge-critical' : (flow.exposure_level === 'High' ? 'badge-advisory' : 'badge-normal')}`;
  }

  // Panel 4: Atmospheric State
  const gPressure = document.getElementById("guidancePressure");
  const gPressTrend = document.getElementById("guidancePressureTendency");
  const gRH = document.getElementById("guidanceRH");
  const gDewPoint = document.getElementById("guidanceDewPoint");
  const gDewSpread = document.getElementById("guidanceDewSpread");
  const gInstab = document.getElementById("guidanceInstabilityProxy");
  const gStateText = document.getElementById("stateGuidanceText");
  const gPressBadge = document.getElementById("pressureTendencyBadge");

  if (gPressure) gPressure.textContent = state.pressure_msl_hpa ?? "--";
  const trend = state.pressure_tendency || {};
  if (gPressTrend) {
    const d3 = trend.delta_3h_hpa ?? 0.0;
    const sign = d3 >= 0 ? "+" : "";
    gPressTrend.textContent = `${sign}${d3.toFixed(1)} hPa (3h)`;
  }
  if (gRH) gRH.textContent = `${state.relative_humidity_pct ?? "--"}%`;
  if (gDewPoint) gDewPoint.textContent = `${state.dew_point_c ?? "--"} °C`;
  const spreadObj = state.dew_point_spread || {};
  if (gDewSpread) gDewSpread.textContent = `${spreadObj.dew_point_spread_c ?? "--"} °C (${spreadObj.saturation_condition ? spreadObj.saturation_condition.split('/')[0].trim() : 'Balanced'})`;
  const instab = state.instability_proxy || {};
  if (gInstab) gInstab.textContent = instab.proxy_value || "Nominal Boundary Layer";
  if (gStateText) gStateText.textContent = trend.synoptic_note || "Stable barometric field within standard semi-diurnal tidal limits.";
  if (gPressBadge) {
    gPressBadge.textContent = trend.tendency || "Steady";
    gPressBadge.className = `badge-saas ${trend.tendency && trend.tendency.includes('Falling') ? 'badge-advisory' : 'badge-normal'}`;
  }

  // Render Forecast Evolution Grid (6h, 24h, 48h, 72h)
  const evoGrid = document.getElementById("guidanceEvolutionGrid");
  if (evoGrid && data.forecast_evolution) {
    evoGrid.innerHTML = "";
    const horizons = ["6h", "24h", "48h", "72h"];
    horizons.forEach(hKey => {
      const hData = data.forecast_evolution[hKey];
      if (!hData) return;
      const card = document.createElement("div");
      card.className = "evolution-card";
      card.innerHTML = `
        <span class="evolution-horizon-badge">+${hKey.toUpperCase()} Projection</span>
        <div class="evolution-cond">${hData.dominant_condition || "Fair Weather"}</div>
        <div class="evolution-metrics">
          <div>Temp: <strong class="font-mono">${hData.expected_temperature_c} °C</strong></div>
          <div>Accumulated Rain: <strong class="font-mono">${hData.expected_rain_accumulation_mm} mm</strong></div>
          <div>Wind Speed: <strong class="font-mono">${hData.expected_wind_speed_kmh} km/h</strong></div>
        </div>
      `;
      evoGrid.appendChild(card);
    });
  }

  // Render Active Triggers
  const triggersContainer = document.getElementById("activeTriggersContainer");
  const countBadge = document.getElementById("triggersCountBadge");
  if (triggersContainer) {
    triggersContainer.innerHTML = "";
    const triggers = data.active_triggers || [];
    if (countBadge) {
      countBadge.textContent = `${triggers.length} Trigger${triggers.length === 1 ? '' : 's'}`;
      countBadge.className = `badge-saas ${triggers.length > 0 ? 'badge-critical' : 'badge-normal'}`;
    }

    if (triggers.length === 0) {
      triggersContainer.innerHTML = `
        <div class="trigger-item" style="border-left: 3px solid var(--color-forest);">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color: var(--color-forest); flex-shrink: 0; margin-top: 2px;"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <div>
            <div class="trigger-indicator-name">All Indicators Nominal</div>
            <div class="trigger-desc">Temperature, rainfall depth, gusts, and barometric gradients are within calibrated baseline operating parameters.</div>
          </div>
        </div>
      `;
    } else {
      triggers.forEach(t => {
        const item = document.createElement("div");
        item.className = "trigger-item";
        item.style.borderLeft = "3px solid var(--color-critical)";
        item.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="color: var(--color-critical); flex-shrink: 0; margin-top: 2px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
          <div>
            <div class="trigger-indicator-name">${t.indicator} &bull; ${t.trigger_value}</div>
            <div class="trigger-desc">${t.reason} (Configured Threshold: ${t.threshold})</div>
          </div>
        `;
        triggersContainer.appendChild(item);
      });
    }
  }

  // Render Computed Indicators Reference Table
  const tableBody = document.getElementById("computedIndicatorsTableBody");
  if (tableBody) {
    const indicatorsRef = [
      {
        name: "Apparent Temperature",
        calc: "Steadman AT + NOAA Rothfusz Heat Index",
        use: "Heat exposure, labor productivity & health protocols",
        val: `${therm.apparent_temperature_c ?? '--'} °C`,
        status: therm.heat_category || "Low"
      },
      {
        name: "Rainfall Accumulation",
        calc: "Temporal integration across 6h, 24h, 48h, 72h windows",
        use: "Waterlogging, urban drainage & agricultural irrigation",
        val: `${precip.accumulation_24h_mm ?? 0} mm / 24h`,
        status: precip.intensity_classification || "Low"
      },
      {
        name: "Rainfall Anomaly",
        calc: "Forecast precipitation vs. 30-year IMD LPA normals",
        use: "Monsoon deficit / excess & regional drought tracking",
        val: `${precip.rainfall_anomaly ? precip.rainfall_anomaly.departure_pct + '%' : '--'}`,
        status: precip.rainfall_anomaly ? precip.rainfall_anomaly.departure_category : "Normal"
      },
      {
        name: "Wind Exposure",
        calc: "Sustained 10m velocity + coastal gust weighting",
        use: "Transport safety, maritime craft & port cargo cranes",
        val: `${flow.wind_speed_kmh ?? 0} km/h (Gusts: ${flow.wind_gusts_kmh ?? 0})`,
        status: flow.exposure_level || "Low"
      },
      {
        name: "Dew-Point Spread",
        calc: "Air temperature minus dew point (T - Td)",
        use: "Boundary-layer saturation, fog & moisture context",
        val: `${spreadObj.dew_point_spread_c ?? '--'} °C`,
        status: spreadObj.saturation_condition ? "Evaluated" : "Nominal"
      },
      {
        name: "Pressure Tendency",
        calc: "3-hour synoptic barometric change (&Delta;P_3h)",
        use: "Localized synoptic context (disclaimer applies)",
        val: `${trend.delta_3h_hpa ?? 0} hPa / 3h`,
        status: trend.tendency || "Steady"
      },
      {
        name: "Dry-Spell Duration",
        calc: "Consecutive forecast days with precipitation < 2.5mm",
        use: "Agricultural sowing schedules & reservoir demand",
        val: `${dryMetrics.consecutive_dry_days ?? 0} Days`,
        status: dryMetrics.status || "Normal"
      }
    ];

    tableBody.innerHTML = "";
    indicatorsRef.forEach(row => {
      const tr = document.createElement("tr");
      const badgeClass = row.status.includes("Severe") || row.status.includes("Heavy") || row.status.includes("Excess")
        ? "badge-critical"
        : (row.status.includes("Moderate") || row.status.includes("High") || row.status.includes("Falling") ? "badge-advisory" : "badge-normal");

      tr.innerHTML = `
        <td><strong>${row.name}</strong></td>
        <td style="font-size: 0.76rem; color: var(--color-text-secondary);">${row.calc}</td>
        <td style="font-size: 0.76rem;">${row.use}</td>
        <td><span class="font-mono" style="font-weight: 600;">${row.val}</span></td>
        <td><span class="badge-saas ${badgeClass}">${row.status}</span></td>
      `;
      tableBody.appendChild(tr);
    });
  }
}

// ------------------------------------------------------------------------------
// Multi-Sector Operational Impact Matrix (Module 2)
// ------------------------------------------------------------------------------

function setupSectorMatrixControls() {
  const filterSelect = document.getElementById("sectorFilterSelect");
  if (filterSelect) {
    filterSelect.addEventListener("change", (e) => {
      currentSectorFilter = e.target.value;
      fetchSectorMatrix(currentDistrictId, currentSectorFilter, currentSectorHorizon, currentSectorSort);
    });
  }

  const horizonBtns = document.querySelectorAll("[data-sector-horizon]");
  horizonBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      horizonBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentSectorHorizon = parseInt(btn.getAttribute("data-sector-horizon"), 10);
      fetchSectorMatrix(currentDistrictId, currentSectorFilter, currentSectorHorizon, currentSectorSort);
    });
  });

  const sortSelect = document.getElementById("sectorSortSelect");
  if (sortSelect) {
    sortSelect.addEventListener("change", (e) => {
      currentSectorSort = e.target.value;
      if (cachedSectorMatrixData) {
        renderSectorMatrix(cachedSectorMatrixData, currentSectorFilter, currentSectorSort);
      }
    });
  }

  const btnExport = document.getElementById("btnExportSectorMatrixCsv");
  if (btnExport) {
    btnExport.addEventListener("click", () => {
      const sectorParam = currentSectorFilter !== "all" ? `&sector=${currentSectorFilter}` : "";
      window.open(`${API_BASE}/api/sectors/matrix/export?horizon=${currentSectorHorizon}${sectorParam}`, "_blank");
      showToast("Downloading Multi-Sector Operational Matrix CSV...", "info");
    });
  }
}

async function fetchSectorMatrix(districtId, sectorFilter = "all", horizon = 24, sortKey = "severity_desc") {
  try {
    const res = await fetch(`${API_BASE}/api/sectors/matrix?district_id=${districtId}&horizon=${horizon}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    cachedSectorMatrixData = data;
    renderSectorMatrix(data, sectorFilter, sortKey);
  } catch (err) {
    console.error("Error fetching sector matrix:", err);
  }
}

function renderSectorMatrix(data, sectorFilter, sortKey) {
  const tbody = document.getElementById("sectorMatrixTableBody");
  if (!tbody || !data || !data.sectors) return;

  tbody.innerHTML = "";
  let sectorsArray = Object.keys(data.sectors).map(key => {
    return { key, ...data.sectors[key] };
  });

  if (sectorFilter && sectorFilter !== "all") {
    sectorsArray = sectorsArray.filter(s => s.key === sectorFilter);
  }

  // Sorting
  const severityRank = { "Severe": 4, "High": 3, "Moderate": 2, "Low": 1 };
  if (sortKey === "severity_desc") {
    sectorsArray.sort((a, b) => (severityRank[b.severity] || 0) - (severityRank[a.severity] || 0) || b.composite_score - a.composite_score);
  } else if (sortKey === "severity_asc") {
    sectorsArray.sort((a, b) => (severityRank[a.severity] || 0) - (severityRank[b.severity] || 0) || a.composite_score - b.composite_score);
  } else if (sortKey === "hazard_desc") {
    sectorsArray.sort((a, b) => b.hazard_likelihood - a.hazard_likelihood);
  } else if (sortKey === "exposure_desc") {
    sectorsArray.sort((a, b) => b.exposure_score - a.exposure_score);
  }

  sectorsArray.forEach(sec => {
    const tr = document.createElement("tr");
    const badgeClass = sec.severity === "Severe"
      ? "badge-critical"
      : (sec.severity === "High" ? "badge-advisory" : "badge-normal");

    tr.innerHTML = `
      <td>
        <strong style="color: var(--color-primary); font-size: 0.88rem;">${sec.sector_name}</strong>
        <div style="font-size: 0.72rem; color: var(--color-text-muted); margin-top: 2px;">
          ${sec.primary_assets_monitored ? sec.primary_assets_monitored.slice(0, 2).join(', ') : ''}
        </div>
      </td>
      <td>
        <span class="font-mono" style="font-weight: 600;">${sec.hazard_likelihood}</span>
        <div class="kpi-linear-gauge" style="margin-top: 4px; width: 60px;">
          <div class="gauge-bar" style="width: ${sec.hazard_likelihood}%; background-color: var(--color-amber);"></div>
        </div>
      </td>
      <td>
        <span class="font-mono" style="font-weight: 600;">${sec.exposure_score}</span>
        <div class="kpi-linear-gauge" style="margin-top: 4px; width: 60px;">
          <div class="gauge-bar" style="width: ${sec.exposure_score}%; background-color: var(--color-ocean);"></div>
        </div>
      </td>
      <td>
        <span class="font-mono" style="font-weight: 600;">${sec.vulnerability_score}</span>
        <div class="kpi-linear-gauge" style="margin-top: 4px; width: 60px;">
          <div class="gauge-bar" style="width: ${sec.vulnerability_score}%; background-color: var(--color-forest);"></div>
        </div>
      </td>
      <td>
        <span class="font-mono" style="font-weight: 700; font-size: 0.95rem; color: var(--color-text);">${sec.composite_score}</span>
        <span style="font-size: 0.7rem; color: var(--color-text-muted);">/100</span>
      </td>
      <td>
        <span class="badge-saas ${badgeClass}">${sec.severity}</span>
      </td>
      <td style="font-size: 0.76rem; color: var(--color-text-secondary); max-width: 200px;">
        ${sec.meteorological_drivers}
      </td>
      <td style="font-size: 0.78rem; color: var(--color-text); max-width: 220px; font-weight: 500;">
        ${sec.potential_operational_impact}
      </td>
      <td style="font-size: 0.78rem; color: var(--color-text); max-width: 260px; line-height: 1.4; background-color: var(--color-surface-muted); padding: 8px 10px; border-radius: var(--radius-sm); border-left: 3px solid var(--color-primary);">
        ${sec.recommended_guidance}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ------------------------------------------------------------------------------
// Settings & Meteorological Data Sources (Module 3)
// ------------------------------------------------------------------------------

function setupSettingsAndSourcesControls() {
  const btnHealth = document.getElementById("btnRefreshSourcesHealth");
  if (btnHealth) {
    btnHealth.addEventListener("click", async () => {
      try {
        const res = await fetch(`${API_BASE}/api/settings/health`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const health = await res.json();
        showToast(`Health Check: ${health.active_sources_count}/${health.total_sources_registered} Sources Active & Operational.`, "success");
        await fetchDataSourcesRegistry();
      } catch (err) {
        console.error("Health check error:", err);
        showToast("Health check failed.", "critical");
      }
    });
  }
}

async function fetchDataSourcesRegistry() {
  try {
    const res = await fetch(`${API_BASE}/api/settings/sources`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const sources = await res.json();
    renderDataSourcesRegistry(sources);
  } catch (err) {
    console.error("Error fetching data sources:", err);
  }
}

function renderDataSourcesRegistry(sources) {
  const tbody = document.getElementById("sourcesRegistryTableBody");
  const countBadge = document.getElementById("sourcesActiveCountBadge");
  if (!tbody || !sources) return;

  const activeCount = sources.filter(s => s.is_enabled).length;
  if (countBadge) {
    countBadge.textContent = `${activeCount}/${sources.length} Active`;
    countBadge.className = `badge-saas ${activeCount >= 3 ? 'badge-normal' : 'badge-advisory'}`;
  }

  tbody.innerHTML = "";
  sources.forEach(src => {
    const tr = document.createElement("tr");
    const varsHtml = src.supported_variables.slice(0, 3).map(v => `<span class="badge-saas badge-normal" style="font-size: 0.68rem; margin: 1px;">${v}</span>`).join(" ");

    tr.innerHTML = `
      <td>
        <strong>${src.name}</strong>
        <div style="font-size: 0.72rem; color: var(--color-text-secondary);">${src.notes || ''}</div>
      </td>
      <td><span class="badge-saas badge-normal font-mono" style="font-size: 0.72rem;">${src.source_type}</span></td>
      <td>
        <a href="${src.endpoint}" target="_blank" rel="noreferrer" style="font-size: 0.75rem; color: var(--color-ocean); text-decoration: underline; word-break: break-all;">
          ${src.endpoint.length > 35 ? src.endpoint.slice(0, 35) + '...' : src.endpoint}
        </a>
      </td>
      <td style="max-width: 200px;">${varsHtml}</td>
      <td style="font-size: 0.75rem; color: var(--color-text-secondary);">${src.update_frequency}</td>
      <td>
        <span class="badge-saas ${src.status === 'ACTIVE' ? 'badge-normal' : 'badge-critical'}">${src.status}</span>
      </td>
      <td><span class="font-mono" style="font-weight: 600;">${src.latency_ms} ms</span></td>
      <td>
        <button class="toggle-switch-btn ${src.is_enabled ? 'active' : 'inactive'}" data-source-toggle="${src.source_id}" data-current-enabled="${src.is_enabled}">
          ${src.is_enabled ? 'Enabled' : 'Disabled'}
        </button>
      </td>
    `;

    const toggleBtn = tr.querySelector("[data-source-toggle]");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => toggleSourceStatusHandler(src.source_id, !src.is_enabled));
    }

    tbody.appendChild(tr);
  });
}

async function toggleSourceStatusHandler(sourceId, newEnabled) {
  try {
    const res = await fetch(`${API_BASE}/api/settings/sources/${sourceId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_enabled: newEnabled, performed_by: "platform_operator" })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    showToast(`Source '${sourceId}' ${newEnabled ? 'Enabled' : 'Disabled'}. Audited in SQLite.`, "success");
    await fetchDataSourcesRegistry();
    await fetchOperationalAuditLog();
  } catch (err) {
    console.error("Toggle source error:", err);
    showToast("Failed to update data source status.", "critical");
  }
}

async function fetchOperationalConfig() {
  try {
    const res = await fetch(`${API_BASE}/api/settings/config`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const config = await res.json();
    renderOperationalConfig(config);
  } catch (err) {
    console.error("Error fetching config:", err);
  }
}

function renderOperationalConfig(config) {
  const container = document.getElementById("operationalConfigParamsGrid");
  if (!container || !config) return;

  container.innerHTML = "";
  Object.keys(config).forEach(key => {
    const item = config[key];
    const row = document.createElement("div");
    row.className = "config-item";
    row.innerHTML = `
      <div class="config-info">
        <span class="config-key">${key}</span>
        <span class="config-desc">${item.description || ''}</span>
      </div>
      <div class="config-action">
        <input type="text" class="config-input" id="cfg_input_${key}" value="${item.value}">
        <button class="btn-save-cfg" data-cfg-key="${key}">Save</button>
      </div>
    `;

    const saveBtn = row.querySelector("[data-cfg-key]");
    if (saveBtn) {
      saveBtn.addEventListener("click", async () => {
        const valInput = document.getElementById(`cfg_input_${key}`);
        if (!valInput) return;
        await updateOperationalSettingHandler(key, valInput.value);
      });
    }

    container.appendChild(row);
  });
}

async function updateOperationalSettingHandler(key, value) {
  try {
    const res = await fetch(`${API_BASE}/api/settings/config`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ setting_key: key, setting_value: value, performed_by: "platform_operator" })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    showToast(`Setting '${key}' saved as '${value}'. Audited in SQLite.`, "success");
    await fetchOperationalConfig();
    await fetchOperationalAuditLog();
  } catch (err) {
    console.error("Update setting error:", err);
    showToast("Failed to update operational setting.", "critical");
  }
}

async function fetchOperationalAuditLog() {
  try {
    const res = await fetch(`${API_BASE}/api/settings/audit?limit=20`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const audit = await res.json();
    renderOperationalAuditLog(audit);
  } catch (err) {
    console.error("Error fetching audit log:", err);
  }
}

function renderOperationalAuditLog(entries) {
  const tbody = document.getElementById("operationalAuditTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (!entries || entries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--color-text-muted); padding: 14px;">No audit events recorded yet.</td></tr>`;
    return;
  }

  entries.forEach(e => {
    const tr = document.createElement("tr");
    const dateFormatted = e.timestamp ? new Date(e.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : '--';

    tr.innerHTML = `
      <td><span class="font-mono" style="font-size: 0.74rem;">#${e.id}</span></td>
      <td><span class="badge-saas badge-normal font-mono" style="font-size: 0.72rem;">${e.action}</span></td>
      <td><code class="font-mono" style="font-size: 0.74rem;">${e.target}</code></td>
      <td><span class="font-mono" style="font-size: 0.74rem; color: var(--color-text-muted);">${e.old_value ?? '--'}</span></td>
      <td><span class="font-mono" style="font-weight: 600; font-size: 0.74rem; color: var(--color-primary);">${e.new_value ?? '--'}</span></td>
      <td><span style="font-size: 0.74rem; font-weight: 500;">${e.performed_by}</span></td>
      <td style="font-size: 0.72rem; color: var(--color-text-muted);">${dateFormatted}</td>
      <td style="font-size: 0.74rem; color: var(--color-text-secondary);">${e.notes || ''}</td>
    `;
    tbody.appendChild(tr);
  });
}

