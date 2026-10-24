"use client";

import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from "react-leaflet";
import L from "leaflet";
import { Compass, Navigation2, Thermometer, Wind } from "lucide-react";

interface NearbySector {
  sector?: string;
  direction?: string;
  label: string;
  distance_km: number;
  latitude: number;
  longitude: number;
  estimated_temperature_c: number;
  estimated_humidity_pct: number;
  wind_speed_kmh: number;
  status: string;
}

interface LiveLeafletMapProps {
  latitude: number;
  longitude: number;
  accuracyM: number;
  nearbySectors: NearbySector[];
  temperature?: number;
  apparentTemperature?: number;
  humidity?: number;
  onSelectSector?: (sector: NearbySector) => void;
}

// Controller component to smoothly fly/pan the map when coordinates update
function RecenterOnCoordinateChange({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    if (lat && lon) {
      map.flyTo([lat, lon], 14, { animate: true, duration: 1.2 });
    }
  }, [lat, lon, map]);
  return null;
}

export default function LiveLeafletMap({
  latitude,
  longitude,
  accuracyM,
  nearbySectors,
  temperature,
  apparentTemperature,
  humidity,
  onSelectSector,
}: LiveLeafletMapProps) {
  // Create custom pulsing SVG marker for device's live GPS position
  const deviceLocationIcon = L.divIcon({
    className: "custom-live-gps-pin",
    html: `
      <div style="position: relative; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;">
        <div style="position: absolute; width: 36px; height: 36px; border-radius: 50%; background: rgba(2, 132, 199, 0.25); animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
        <div style="position: absolute; width: 22px; height: 22px; border-radius: 50%; background: #0284C7; border: 3px solid #FFFFFF; box-shadow: 0 2px 8px rgba(0,0,0,0.25); display: flex; align-items: center; justify-content: center;">
          <div style="width: 6px; height: 6px; border-radius: 50%; background: #FFFFFF;"></div>
        </div>
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  });

  // Create sector pin icons with cardinal letters and temperatures
  const createSectorIcon = (sector: string, temp: number) => {
    return L.divIcon({
      className: "custom-sector-pin",
      html: `
        <div style="background: #FFFFFF; border: 1.5px solid #0A5C59; border-radius: 9999px; padding: 2px 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.12); display: flex; align-items: center; gap: 4px; font-family: sans-serif; font-size: 11px; font-weight: 700; color: #0A5C59; white-space: nowrap;">
          <span style="background: #E6FAF9; border-radius: 9999px; padding: 1px 5px; font-size: 9px; color: #0A5C59;">${sector}</span>
          <span>${temp}°C</span>
        </div>
      `,
      iconSize: [70, 26],
      iconAnchor: [35, 13],
      popupAnchor: [0, -14],
    });
  };

  return (
    <div className="relative w-full h-[400px] sm:h-[480px] rounded-2xl overflow-hidden border border-border-subtle shadow-sm bg-canvas-subtle">
      <MapContainer
        center={[latitude, longitude]}
        zoom={13}
        scrollWheelZoom={false}
        className="w-full h-full z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />

        <RecenterOnCoordinateChange lat={latitude} lon={longitude} />

        {/* Live Device Accuracy Radius Circle */}
        <Circle
          center={[latitude, longitude]}
          radius={Math.max(accuracyM || 25, 20)}
          pathOptions={{
            color: "#0284C7",
            fillColor: "#0284C7",
            fillOpacity: 0.12,
            weight: 1.5,
            dashArray: "4, 4",
          }}
        />

        {/* Device Live Marker */}
        <Marker position={[latitude, longitude]} icon={deviceLocationIcon}>
          <Popup className="custom-leaflet-popup">
            <div className="p-1 font-sans text-xs min-w-[180px]">
              <div className="flex items-center gap-1.5 font-bold text-ink-primary border-b border-border-subtle pb-1 mb-1.5">
                <Navigation2 className="w-3.5 h-3.5 text-brand-sky" />
                <span>Your Real-Time Device Position</span>
              </div>
              <div className="space-y-1 text-ink-secondary">
                <div className="flex justify-between">
                  <span>Coordinates:</span>
                  <span className="font-mono font-medium text-ink-primary">
                    {latitude.toFixed(4)}°, {longitude.toFixed(4)}°
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>GPS Accuracy:</span>
                  <span className="font-medium text-brand-sky">
                    ±{Math.round(accuracyM || 18)} meters
                  </span>
                </div>
                {temperature !== undefined && (
                  <div className="flex justify-between pt-1 border-t border-border-subtle">
                    <span>Surrounding Temp:</span>
                    <span className="font-bold text-ink-primary">{temperature}°C</span>
                  </div>
                )}
                {apparentTemperature !== undefined && (
                  <div className="flex justify-between">
                    <span>Feels Like:</span>
                    <span className="font-medium text-ink-primary">{apparentTemperature}°C</span>
                  </div>
                )}
              </div>
            </div>
          </Popup>
        </Marker>

        {/* Cardinal Surrounding Microclimate Markers (+5 km) */}
        {nearbySectors
          .filter((s) => s.distance_km > 0)
          .map((sector) => {
            const sectorCode =
              sector.sector ||
              (sector.direction ? sector.direction.charAt(0) : "S");
            return (
              <Marker
                key={`${sector.latitude}-${sector.longitude}`}
                position={[sector.latitude, sector.longitude]}
                icon={createSectorIcon(sectorCode, sector.estimated_temperature_c)}
                eventHandlers={{
                  click: () => onSelectSector && onSelectSector(sector),
                }}
              >
            <Popup className="custom-leaflet-popup">
              <div className="p-1 font-sans text-xs min-w-[170px]">
                <div className="font-bold text-ink-primary mb-1">
                  {sector.label}
                </div>
                <div className="space-y-1 text-ink-secondary">
                  <div className="flex justify-between">
                    <span>Distance:</span>
                    <span className="font-medium text-ink-primary">{sector.distance_km} km</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Est. Temperature:</span>
                    <span className="font-bold text-ink-primary">{sector.estimated_temperature_c}°C</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Est. Humidity:</span>
                    <span className="font-medium text-ink-primary">{sector.estimated_humidity_pct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Wind Speed:</span>
                    <span className="font-medium text-ink-primary">{sector.wind_speed_kmh} km/h</span>
                  </div>
                </div>
              </div>
            </Popup>
          </Marker>
        );
      })}
      </MapContainer>

      {/* Floating Legend Badge */}
      <div className="absolute bottom-3 left-3 z-[400] bg-white/90 backdrop-blur-md px-3 py-2 rounded-xl border border-border-subtle shadow-md text-[11px] text-ink-secondary flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-brand-sky border border-white"></span>
          <span>Live GPS Position (±{Math.round(accuracyM || 18)}m)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-brand-deepTeal"></span>
          <span>Microclimate Sectors (+5km)</span>
        </div>
      </div>
    </div>
  );
}
