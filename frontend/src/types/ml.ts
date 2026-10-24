export interface MLDatasetItem {
  id: string;
  location_id: string;
  source: string;
  data_kind: string;
  file_path: string;
  start_date: string;
  end_date: string;
  retrieved_at: string;
  row_count: number;
  has_parquet: boolean;
  metadata?: {
    models?: string;
    resolution?: string;
    variables?: string[];
    parquet_path?: string;
    csv_path?: string;
  };
}

export interface MLModelMetrics {
  mae: number;
  rmse: number;
  mse: number;
  r2: number;
  skill_score_pct?: number;
}

export interface MLBaselineMetrics {
  baseline_type: string;
  mae: number;
  rmse: number;
  mse: number;
  r2: number;
}

export interface MLModelItem {
  id: string;
  name: string;
  dataset_id: string;
  location_id: string;
  target_variable: string;
  horizon_hours: number;
  algorithm: string;
  file_path: string;
  train_rows: number;
  test_rows: number;
  metrics: MLModelMetrics;
  baseline_metrics: MLBaselineMetrics;
  created_at: string;
}

export interface MLTrainResponse {
  id: string;
  name: string;
  dataset_id: string;
  location_id: string;
  target_variable: string;
  horizon_hours: number;
  algorithm: string;
  metrics: MLModelMetrics;
  baseline_metrics: MLBaselineMetrics;
  splits: {
    train_count: number;
    val_count: number;
    test_count: number;
    total_count: number;
  };
  created_at: string;
}
