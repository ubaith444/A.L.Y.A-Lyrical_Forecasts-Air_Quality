import { LocationData, ProvenanceData } from "./weather";

export interface PollutantDetail {
  value: number | null;
  unit: string | null;
  status: "available" | "unavailable";
  sub_index?: number | null;
}

export interface CPCBDetails {
  value: number;
  category: "Good" | "Satisfactory" | "Moderate" | "Poor" | "Very Poor" | "Severe";
  standard: string;
  dominant_pollutant: string;
  sub_indices: Record<string, number>;
  averages_used: Record<string, number>;
  health_guidance: string;
  status: string;
  method: string;
}

export interface AQIData {
  value: number | null;
  standard: string;
  provider_value: string;
  indian_aqi: number | null;
  indian_aqi_status: string;
  european_aqi?: number | null;
  cpcb_details?: CPCBDetails | null;
  standards_disclaimer: string;
}

export interface AirQualityResponse {
  location: LocationData;
  timestamp: string | null;
  aqi: AQIData;
  pollutants: {
    pm2_5: PollutantDetail;
    pm10: PollutantDetail;
    nitrogen_dioxide: PollutantDetail;
    ozone: PollutantDetail;
    sulphur_dioxide: PollutantDetail;
    carbon_monoxide: PollutantDetail;
    [key: string]: PollutantDetail;
  };
  health_guidance: {
    category: string;
    message: string;
    standard: string;
    [key: string]: string;
  };
  data_quality: {
    status: string;
    notes: string;
  };
  provenance: ProvenanceData;
}
