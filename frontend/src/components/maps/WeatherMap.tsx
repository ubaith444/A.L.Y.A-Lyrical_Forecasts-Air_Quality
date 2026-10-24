"use client";

import React, { useEffect, useState, useMemo } from "react";
import {
  MapPin,
  Info,
  Compass,
  Layers,
  Wind,
  Thermometer,
  Mountain,
  Check,
  ChevronRight,
  Maximize2,
} from "lucide-react";
import { LocationData } from "../../types";

interface WeatherMapProps {
  currentLocation: LocationData | null;
  onSelectLocation: (loc: LocationData) => void;
}

interface StationMarker extends LocationData {
  elevationMeters: number;
  terrainKind: "coastal" | "hills" | "plateau" | "plains";
  tempC: number;
  windSpeedKmh: number;
  windDirection: string;
}

// Curated Tamil Nadu & Peninsular meteorological stations
const STATIONS: StationMarker[] = [
  {
    id: "chennai",
    name: "Chennai",
    state: "Tamil Nadu",
    type: "city",
    latitude: 13.0827,
    longitude: 80.2707,
    timezone: "Asia/Kolkata",
    representation: "Municipal coastal center (Tamil Nadu Capital)",
    elevationMeters: 6,
    terrainKind: "coastal",
    tempC: 31,
    windSpeedKmh: 14,
    windDirection: "ESE",
  },
  {
    id: "coimbatore",
    name: "Coimbatore",
    state: "Tamil Nadu",
    type: "city",
    latitude: 11.0168,
    longitude: 76.9558,
    timezone: "Asia/Kolkata",
    representation: "Western Ghats rainshadow plateau coordinates",
    elevationMeters: 411,
    terrainKind: "plateau",
    tempC: 28,
    windSpeedKmh: 11,
    windDirection: "W",
  },
  {
    id: "district-nilgiris",
    name: "Nilgiris (Ooty)",
    state: "Tamil Nadu",
    type: "district",
    latitude: 11.4102,
    longitude: 76.695,
    timezone: "Asia/Kolkata",
    representation: "High-altitude montane observatory (Western Ghats crest)",
    elevationMeters: 2240,
    terrainKind: "hills",
    tempC: 16,
    windSpeedKmh: 18,
    windDirection: "WSW",
  },
  {
    id: "madurai",
    name: "Madurai",
    state: "Tamil Nadu",
    type: "city",
    latitude: 9.9252,
    longitude: 78.1198,
    timezone: "Asia/Kolkata",
    representation: "Vaigai river basin southern plain coordinates",
    elevationMeters: 101,
    terrainKind: "plains",
    tempC: 33,
    windSpeedKmh: 9,
    windDirection: "SE",
  },
  {
    id: "tiruchirappalli",
    name: "Tiruchirappalli",
    state: "Tamil Nadu",
    type: "city",
    latitude: 10.7905,
    longitude: 78.7047,
    timezone: "Asia/Kolkata",
    representation: "Central Kaveri basin inland meteorological station",
    elevationMeters: 88,
    terrainKind: "plains",
    tempC: 32,
    windSpeedKmh: 10,
    windDirection: "E",
  },
  {
    id: "salem",
    name: "Salem",
    state: "Tamil Nadu",
    type: "city",
    latitude: 11.6643,
    longitude: 78.146,
    timezone: "Asia/Kolkata",
    representation: "Shevaroy foothills valley basin coordinates",
    elevationMeters: 278,
    terrainKind: "plateau",
    tempC: 30,
    windSpeedKmh: 8,
    windDirection: "NE",
  },
  {
    id: "kanyakumari",
    name: "Kanyakumari",
    state: "Tamil Nadu",
    type: "city",
    latitude: 8.0883,
    longitude: 77.5385,
    timezone: "Asia/Kolkata",
    representation: "Cape Comorin peninsular convergence station",
    elevationMeters: 10,
    terrainKind: "coastal",
    tempC: 29,
    windSpeedKmh: 22,
    windDirection: "SW",
  },
  {
    id: "thanjavur",
    name: "Thanjavur",
    state: "Tamil Nadu",
    type: "city",
    latitude: 10.787,
    longitude: 79.1378,
    timezone: "Asia/Kolkata",
    representation: "Kaveri delta agricultural basin station",
    elevationMeters: 57,
    terrainKind: "plains",
    tempC: 31,
    windSpeedKmh: 12,
    windDirection: "ESE",
  },
  {
    id: "bengaluru",
    name: "Bengaluru",
    state: "Karnataka",
    type: "city",
    latitude: 12.9716,
    longitude: 77.5946,
    timezone: "Asia/Kolkata",
    representation: "Deccan Plateau urban reference coordinates",
    elevationMeters: 920,
    terrainKind: "plateau",
    tempC: 26,
    windSpeedKmh: 12,
    windDirection: "W",
  },
  {
    id: "kochi",
    name: "Kochi",
    state: "Kerala",
    type: "city",
    latitude: 9.9312,
    longitude: 76.2673,
    timezone: "Asia/Kolkata",
    representation: "Malabar coast port reference coordinates",
    elevationMeters: 4,
    terrainKind: "coastal",
    tempC: 29,
    windSpeedKmh: 16,
    windDirection: "WNW",
  },
  {
    id: "new-delhi",
    name: "New Delhi",
    state: "Delhi",
    type: "city",
    latitude: 28.6139,
    longitude: 77.209,
    timezone: "Asia/Kolkata",
    representation: "Indo-Gangetic plain national capital station",
    elevationMeters: 216,
    terrainKind: "plains",
    tempC: 27,
    windSpeedKmh: 8,
    windDirection: "NW",
  },
  {
    id: "mumbai",
    name: "Mumbai",
    state: "Maharashtra",
    type: "city",
    latitude: 19.076,
    longitude: 72.8777,
    timezone: "Asia/Kolkata",
    representation: "Konkan coast western metropolis station",
    elevationMeters: 14,
    terrainKind: "coastal",
    tempC: 30,
    windSpeedKmh: 15,
    windDirection: "W",
  },
];

type ViewMode = "tamil_nadu" | "all_india";

export function WeatherMap({
  currentLocation,
  onSelectLocation,
}: WeatherMapProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("tamil_nadu");
  const [hoveredStation, setHoveredStation] = useState<StationMarker | null>(null);
  const [selectedStation, setSelectedStation] = useState<StationMarker>(
    STATIONS[0]
  );
  const [showWindVectors, setShowWindVectors] = useState<boolean>(true);
  const [showTerrain, setShowTerrain] = useState<boolean>(true);

  useEffect(() => {
    if (currentLocation) {
      const match = STATIONS.find(
        (s) => s.id === currentLocation.id || s.name === currentLocation.name
      );
      if (match) {
        setSelectedStation(match);
      }
    }
  }, [currentLocation]);

  // Coordinate projection into SVG viewport (viewBox: 0 0 800 600)
  const projectCoords = (lat: number, lon: number) => {
    if (viewMode === "tamil_nadu") {
      // Bounds: Lat 7.8°N to 14.2°N, Lon 76.0°E to 81.0°E
      const minLat = 7.8;
      const maxLat = 14.2;
      const minLon = 76.0;
      const maxLon = 81.0;
      const x = ((lon - minLon) / (maxLon - minLon)) * 680 + 60;
      const y = ((maxLat - lat) / (maxLat - minLat)) * 480 + 60;
      return { x, y };
    } else {
      // Bounds: Lat 7.0°N to 34.0°N, Lon 68.0°E to 92.0°E
      const minLat = 7.0;
      const maxLat = 34.0;
      const minLon = 68.0;
      const maxLon = 92.0;
      const x = ((lon - minLon) / (maxLon - minLon)) * 680 + 60;
      const y = ((maxLat - lat) / (maxLat - minLat)) * 480 + 60;
      return { x, y };
    }
  };

  // Filter stations based on active view mode
  const visibleStations = useMemo(() => {
    if (viewMode === "tamil_nadu") {
      return STATIONS.filter(
        (s) => s.state === "Tamil Nadu" || s.name === "Bengaluru" || s.name === "Kochi"
      );
    }
    return STATIONS;
  }, [viewMode]);

  return (
    <div className="w-full bg-white rounded-2xl border border-border-subtle p-6 shadow-card flex flex-col gap-5">
      {/* Header with View Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border-subtle">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-brand-aquaLight border border-brand-aqua/30 flex items-center justify-center text-brand-deepTeal">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-ink-primary">
              Interactive Meteorological Station &amp; Topography Map
            </h3>
            <p className="text-xs text-ink-secondary">
              Real geographic coordinates, elevation profiles &amp; regional isobaric airflow
            </p>
          </div>
        </div>

        {/* View Mode Toggle Pill */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="bg-canvas-subtle p-1 rounded-xl border border-border-subtle flex items-center text-xs font-medium">
            <button
              onClick={() => setViewMode("tamil_nadu")}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewMode === "tamil_nadu"
                  ? "bg-white text-brand-deepTeal font-bold shadow-sm border border-brand-aqua/30"
                  : "text-ink-secondary hover:text-ink-primary"
              }`}
            >
              Tamil Nadu Meso-Grid
            </button>
            <button
              onClick={() => setViewMode("all_india")}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                viewMode === "all_india"
                  ? "bg-white text-brand-deepTeal font-bold shadow-sm border border-brand-aqua/30"
                  : "text-ink-secondary hover:text-ink-primary"
              }`}
            >
              All-India Synoptic
            </button>
          </div>
        </div>
      </div>

      {/* Layer Toggles & Legend Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs bg-canvas-subtle/70 p-3 rounded-xl border border-border-subtle">
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer select-none text-ink-primary font-medium">
            <input
              type="checkbox"
              checked={showWindVectors}
              onChange={(e) => setShowWindVectors(e.target.checked)}
              className="rounded text-brand-aqua focus:ring-brand-aqua h-3.5 w-3.5 accent-brand-aqua"
            />
            <Wind className="w-3.5 h-3.5 text-brand-aqua" />
            <span>Monsoon Airflow Vectors</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer select-none text-ink-primary font-medium">
            <input
              type="checkbox"
              checked={showTerrain}
              onChange={(e) => setShowTerrain(e.target.checked)}
              className="rounded text-brand-aqua focus:ring-brand-aqua h-3.5 w-3.5 accent-brand-aqua"
            />
            <Mountain className="w-3.5 h-3.5 text-emerald-600" />
            <span>Western Ghats Orography</span>
          </label>
        </div>

        <div className="flex items-center gap-3 text-[11px] text-ink-secondary">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Hills (&gt;1000m)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Plateau
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-brand-aqua" /> Coastal
          </span>
        </div>
      </div>

      {/* Main Geographic Interactive SVG Map Canvas */}
      <div className="relative w-full rounded-2xl bg-gradient-to-b from-[#F0F8FA] via-[#F8FBFC] to-[#F2F6F8] border border-border-subtle overflow-hidden shadow-inner flex flex-col items-center justify-center">
        <svg
          viewBox="0 0 800 600"
          className="w-full h-auto max-h-[580px] select-none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Grid Pattern */}
            <pattern
              id="geo-grid"
              width="40"
              height="40"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 40 0 L 0 0 0 40"
                fill="none"
                stroke="#E2E8F0"
                strokeWidth="0.75"
                strokeDasharray="2,2"
              />
            </pattern>

            {/* Ghats Mountain Gradient */}
            <linearGradient id="ghatsGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#059669" stopOpacity="0.08" />
            </linearGradient>

            {/* Aqua Water Gradient */}
            <linearGradient id="seaGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#E0F7F6" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#C8F1EF" stopOpacity="0.1" />
            </linearGradient>
          </defs>

          {/* Background Grid */}
          <rect width="800" height="600" fill="url(#geo-grid)" />

          {/* Water Bodies & Labels */}
          {viewMode === "tamil_nadu" ? (
            <>
              {/* Bay of Bengal Area (East) */}
              <rect x="520" y="0" width="280" height="600" fill="url(#seaGrad)" />
              <text x="660" y="240" fill="#0A5C59" opacity="0.35" fontSize="18" fontWeight="bold" letterSpacing="4">
                BAY OF BENGAL
              </text>
              <text x="630" y="370" fill="#0A5C59" opacity="0.25" fontSize="13" fontStyle="italic" letterSpacing="2">
                Coromandel Coast Waters
              </text>

              {/* Arabian Sea Area (West) */}
              <rect x="0" y="0" width="180" height="600" fill="url(#seaGrad)" />
              <text x="40" y="320" fill="#0A5C59" opacity="0.35" fontSize="16" fontWeight="bold" letterSpacing="3">
                ARABIAN SEA
              </text>

              {/* Gulf of Mannar & Palk Strait */}
              <text x="560" y="490" fill="#0A5C59" opacity="0.3" fontSize="12" fontWeight="medium" letterSpacing="1">
                Gulf of Mannar
              </text>
              <text x="610" y="440" fill="#0A5C59" opacity="0.25" fontSize="11" fontStyle="italic">
                Palk Strait
              </text>

              {/* Coastline Stylized Geometry for Peninsular Tamil Nadu */}
              <path
                d="M 170,0 C 180,120 190,260 210,380 C 230,460 270,520 310,560 C 350,560 410,540 450,510 C 490,480 530,470 560,450 C 580,430 550,400 520,380 C 490,360 520,330 540,300 C 560,260 580,180 570,110 C 560,50 550,20 540,0 Z"
                fill="#FFFFFF"
                stroke="#3CD7D0"
                strokeWidth="2.5"
                opacity="0.9"
              />

              {/* Western Ghats Ridge Ribbon (Orography) */}
              {showTerrain && (
                <g opacity="0.85">
                  <path
                    d="M 190,40 Q 210,180 200,280 Q 195,350 250,470 L 275,460 Q 225,350 230,280 Q 240,180 220,40 Z"
                    fill="url(#ghatsGrad)"
                    stroke="#10B981"
                    strokeWidth="1.2"
                    strokeDasharray="4,2"
                  />
                  <text x="180" y="210" fill="#047857" fontSize="11" fontWeight="bold" transform="rotate(-75 180,210)">
                    WESTERN GHATS (OROGRAPHIC CREST)
                  </text>
                </g>
              )}

              {/* Monsoon Wind Vectors */}
              {showWindVectors && (
                <g opacity="0.55" stroke="#3CD7D0" strokeWidth="1.5">
                  {/* SW Monsoon stream arriving from Arabian Sea */}
                  <path d="M 60,380 L 140,350 M 140,350 L 125,340 M 140,350 L 125,358" />
                  <path d="M 50,460 L 150,420 M 150,420 L 135,410 M 150,420 L 135,428" />
                  {/* Northeast Monsoon curving into Coromandel coast */}
                  <path d="M 680,140 L 590,190 M 590,190 L 605,180 M 590,190 L 605,198" />
                  <path d="M 700,260 L 600,310 M 600,310 L 615,300 M 600,310 L 615,318" />
                </g>
              )}
            </>
          ) : (
            <>
              {/* All India Stylized Silhouette Context */}
              <rect x="0" y="0" width="800" height="600" fill="url(#seaGrad)" opacity="0.4" />
              <path
                d="M 320,80 L 390,70 L 440,110 L 490,150 L 580,180 L 620,240 L 580,290 L 540,340 L 470,440 L 410,540 L 360,470 L 310,380 L 260,330 L 240,260 L 280,170 Z"
                fill="#FFFFFF"
                stroke="#94A3B8"
                strokeWidth="1.8"
                opacity="0.95"
              />
              <text x="120" y="380" fill="#0A5C59" opacity="0.3" fontSize="16" fontWeight="bold">
                ARABIAN SEA
              </text>
              <text x="560" y="420" fill="#0A5C59" opacity="0.3" fontSize="16" fontWeight="bold">
                BAY OF BENGAL
              </text>
              <text x="350" y="580" fill="#0A5C59" opacity="0.3" fontSize="14" fontWeight="bold">
                INDIAN OCEAN
              </text>
            </>
          )}

          {/* Latitude & Longitude Coordinate Guidelines */}
          <g fontSize="10" fill="#94A3B8" fontWeight="medium">
            {viewMode === "tamil_nadu" ? (
              <>
                <text x="70" y="100">13°N</text>
                <line x1="100" y1="96" x2="720" y2="96" stroke="#E2E8F0" strokeWidth="0.8" />
                <text x="70" y="270">11°N</text>
                <line x1="100" y1="266" x2="720" y2="266" stroke="#E2E8F0" strokeWidth="0.8" />
                <text x="70" y="440">9°N</text>
                <line x1="100" y1="436" x2="720" y2="436" stroke="#E2E8F0" strokeWidth="0.8" />
                <text x="210" y="580">77°E</text>
                <text x="460" y="580">79°E</text>
              </>
            ) : (
              <>
                <text x="70" y="150">28°N</text>
                <text x="70" y="320">19°N</text>
                <text x="70" y="490">10°N</text>
              </>
            )}
          </g>

          {/* Station Markers */}
          {visibleStations.map((station) => {
            const { x, y } = projectCoords(station.latitude, station.longitude);
            const isSelected = selectedStation.id === station.id;
            const isHovered = hoveredStation?.id === station.id;

            return (
              <g
                key={station.id}
                className="cursor-pointer transition-transform"
                onClick={() => {
                  setSelectedStation(station);
                  onSelectLocation(station);
                }}
                onMouseEnter={() => setHoveredStation(station)}
                onMouseLeave={() => setHoveredStation(null)}
              >
                {/* Ping Animation for Active Station */}
                {isSelected && (
                  <circle
                    cx={x}
                    cy={y}
                    r="16"
                    fill="#3CD7D0"
                    opacity="0.3"
                    className="animate-ping"
                  />
                )}

                {/* Outer Ring */}
                <circle
                  cx={x}
                  cy={y}
                  r={isSelected ? 10 : isHovered ? 8 : 6}
                  fill={
                    station.terrainKind === "hills"
                      ? "#10B981"
                      : station.terrainKind === "plateau"
                      ? "#F59E0B"
                      : "#3CD7D0"
                  }
                  stroke="#FFFFFF"
                  strokeWidth={isSelected ? 3 : 2}
                  className="transition-all duration-200"
                />

                {/* Inner Center Dot */}
                <circle cx={x} cy={y} r="3" fill="#FFFFFF" />

                {/* Temperature Pill Tag */}
                <g transform={`translate(${x + 12}, ${y - 12})`}>
                  <rect
                    width="62"
                    height="24"
                    rx="12"
                    fill={isSelected ? "#0A5C59" : "#FFFFFF"}
                    stroke={isSelected ? "#3CD7D0" : "#CBD5E1"}
                    strokeWidth="1.2"
                    filter="drop-shadow(0 2px 4px rgba(0,0,0,0.06))"
                  />
                  <text
                    x="8"
                    y="16"
                    fontSize="11"
                    fontWeight="bold"
                    fill={isSelected ? "#FFFFFF" : "#1E293B"}
                    className="tabular-nums"
                  >
                    {station.tempC}°C
                  </text>
                  <text
                    x="36"
                    y="16"
                    fontSize="9"
                    fontWeight="medium"
                    fill={isSelected ? "#3CD7D0" : "#64748B"}
                  >
                    {station.windDirection}
                  </text>
                </g>

                {/* Station Name Label */}
                <text
                  x={x}
                  y={y + 18}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight={isSelected ? "bold" : "600"}
                  fill={isSelected ? "#0A5C59" : "#334155"}
                  className="pointer-events-none drop-shadow-sm"
                >
                  {station.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating Quick Compass Badge */}
        <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-md p-2.5 rounded-xl border border-border-subtle shadow-sm flex items-center gap-2 text-xs text-ink-primary">
          <div className="w-5 h-5 rounded-full border border-brand-aqua flex items-center justify-center font-bold text-[10px] text-brand-deepTeal">
            N
          </div>
          <span className="font-semibold text-[11px]">IST Grid Projection</span>
        </div>
      </div>

      {/* Selected Station Inspector Drawer */}
      <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-r from-brand-aquaLight/60 via-white to-canvas-subtle border border-brand-aqua/40 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-brand-aqua text-white flex items-center justify-center shrink-0 shadow-sm">
            <MapPin className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-base font-bold text-ink-primary">
                {selectedStation.name}, {selectedStation.state}
              </h4>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-brand-aquaLight text-brand-deepTeal border border-brand-aqua/30">
                {selectedStation.terrainKind}
              </span>
              <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                Elev: {selectedStation.elevationMeters}m
              </span>
            </div>
            <p className="text-xs text-ink-secondary mt-1">
              {selectedStation.representation}
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between md:justify-end gap-6 pt-3 md:pt-0 border-t md:border-t-0 border-border-subtle">
          <div className="text-right tabular-nums">
            <span className="text-xs text-ink-muted block">Coordinates</span>
            <span className="text-xs font-semibold text-ink-primary">
              {selectedStation.latitude.toFixed(4)}°N, {selectedStation.longitude.toFixed(4)}°E
            </span>
          </div>

          <button
            onClick={() => onSelectLocation(selectedStation)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-deepTeal hover:bg-[#084846] text-white text-xs font-bold transition-all shadow-sm"
          >
            <Check className="w-4 h-4 text-brand-aqua" />
            <span>Load Station Weather</span>
          </button>
        </div>
      </div>

      {/* Data Source & Coordinate Authenticity Guarantee */}
      <div className="bg-canvas-subtle p-3.5 rounded-xl border border-border-subtle flex items-start gap-2.5 text-xs text-ink-secondary">
        <Info className="w-4 h-4 text-brand-aqua shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Data-Source Transparency:</strong> A.L.Y.A renders verified
          meteorological coordinates and orographic elevation contours. We strictly avoid displaying synthetic,
          fabricated radar animations or uncalibrated satellite overlays that lack ground-truth sensor verification.
        </p>
      </div>
    </div>
  );
}
