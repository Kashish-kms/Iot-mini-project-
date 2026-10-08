export interface TelemetryReading {
  id: number;
  timestamp: string;
  temperature: number;
  humidity: number;
  air_quality_ppm: number;
  motion_detected: number;
  motion_count: number;
  fan_active: number;
  risk_level: number; // 0: Safe, 1: Moderate, 2: High Risk
  risk_confidence: number;
  is_outlier: number;
  device_id: string;
}

export interface RiskPrediction {
  risk_level: number;
  risk_label: string;
  confidence: number;
  probabilities: {
    Safe: number;
    Moderate: number;
    "High Risk": number;
  };
  top_contributing_factors: Array<{
    factor: string;
    impact: string;
    contribution: string;
  }>;
  recommendations: string[];
}

export interface SensorStatus {
  status: string;
  pin: number;
  last_read_ms?: number;
  heater_resistance_ohms?: number;
  interrupt_count?: number;
}

export interface DeviceStatus {
  device_id: string;
  online: boolean;
  ip_address: string;
  wifi_rssi_dbm: number;
  firmware_version: string;
  uptime_seconds: number;
  free_heap_bytes: number;
  sampling_interval_sec: number;
  tls_secured: boolean;
  tls_cipher: string;
  sensors: {
    dht22: SensorStatus;
    mq135: SensorStatus;
    pir: SensorStatus;
  };
  last_seen: string;
}

export interface AlertItem {
  id: number;
  timestamp: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  resolved: number;
}

export interface ModelMetricDetails {
  model_name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  latency_ms: number;
  confusion_matrix: number[][];
}

export interface ModelMetricsReport {
  timestamp: string;
  dataset_size_clean: number;
  dataset_size_raw: number;
  outliers_removed: number;
  feature_names: string[];
  feature_importance: Array<{
    feature: string;
    importance: number;
  }>;
  models: {
    baseline: ModelMetricDetails;
    logistic_regression: ModelMetricDetails;
    random_forest: ModelMetricDetails;
  };
  best_model: string;
}

export interface EdaInsights {
  statistics: {
    temperature: { min: number; max: number; mean: number; std?: number };
    humidity: { min: number; max: number; mean: number; std?: number };
    air_quality_ppm: { min: number; max: number; mean: number; std?: number };
    total_samples: number;
    outlier_count?: number;
  };
  correlation_matrix: {
    columns: string[];
    values: number[][];
  };
  hourly_patterns: Array<{
    hour: number;
    temperature: number;
    humidity: number;
    air_quality_ppm: number;
    motion_detected: number;
  }>;
  label_distribution: Array<{
    label: string;
    value: number;
    percentage: number;
  }>;
  histograms?: Record<string, Array<{ range: string; count: number }>>;
}
