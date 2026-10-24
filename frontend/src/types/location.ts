import { LocationData } from "./weather";

export interface LocationsResponse {
  items: LocationData[];
  pagination: {
    offset: number;
    limit: number;
    total: number;
  };
  catalogue_coverage: string;
}

export interface StateRecord {
  state: string;
  locations_count: number;
  has_state_record: boolean;
  latitude?: number;
  longitude?: number;
}

export interface StatesResponse {
  items: StateRecord[];
  total: number;
  note: string;
}

export interface DataSourceItem {
  id: string;
  name: string;
  kind: string;
  url: string;
  limitations: string;
}

export interface DataSourcesResponse {
  items: DataSourceItem[];
}
