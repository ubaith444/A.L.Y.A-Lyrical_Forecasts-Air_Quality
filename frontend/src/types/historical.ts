export interface HistoricalDataset {
  id: string;
  location_id: string;
  source: string;
  data_kind: string;
  start_date: string;
  end_date: string;
  retrieved_at: string;
  row_count: number;
  metadata: {
    location: {
      id: string;
      name: string;
      state: string;
      latitude: number;
      longitude: number;
    };
    variables: string[];
    units: Record<string, string>;
    provider: string;
    source_kind: string;
    processing: string;
  };
}

export interface SummaryItem {
  period: string;
  count: number;
  mean: number;
  total?: number | null;
  min: number;
  max: number;
  anomaly?: number;
}

export interface HistoricalSummaryResponse {
  dataset_id: string;
  variable: string;
  unit: string;
  period: "daily" | "monthly" | "seasonal" | "annual";
  items: SummaryItem[];
  source_note: string;
  baseline?: {
    dataset_id: string;
    mean: number;
    anomaly_method: string;
  };
}

export interface MonsoonResponse {
  dataset_id: string;
  variable: string;
  unit: string;
  period: {
    start_month: number;
    end_month: number;
  };
  days_with_data: number;
  rainfall_total: number | null;
  note: string;
}

export interface HeatPatternsResponse {
  dataset_id: string;
  threshold_celsius: number;
  unit: string;
  total_days_analyzed: number;
  days_above_35c: number;
  days_above_40c: number;
  days_above_45c: number;
  days_above_threshold: number;
  max_consecutive_hot_days: number;
  peak_temperature: {
    temperature: number;
    date: string;
  };
  lowest_daily_max: {
    temperature: number;
    date: string;
  };
  mean_temperature: number;
  summer_season_summary: {
    months: string;
    days_with_data: number;
    mean_temperature: number | null;
    hot_days_count: number;
  };
  monthly_hot_days: Record<string, number>;
  source_note: string;
}

export interface ComparisonResponse {
  variable: string;
  unit: string;
  left: {
    dataset_id: string;
    location_id: string;
    mean: number;
  };
  right: {
    dataset_id: string;
    location_id: string;
    mean: number;
  };
  difference_left_minus_right: number;
  note: string;
}
