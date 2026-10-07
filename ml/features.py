"""
VeilSense Feature Engineering & Preprocessing Pipeline
Provides IQR outlier filtering, rolling statistics, rate-of-change,
comfort indexes, and temporal cyclical features.
"""

import numpy as np
import pandas as pd

def detect_outliers_iqr(df, columns=['temperature', 'humidity', 'air_quality_ppm'], factor=1.5):
    """
    Identifies outliers using the Interquartile Range (IQR) method.
    Returns a boolean series where True indicates an outlier.
    """
    outlier_mask = pd.Series(False, index=df.index)
    for col in columns:
        if col in df.columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - factor * iqr
            upper_bound = q3 + factor * iqr
            outlier_mask = outlier_mask | (df[col] < lower_bound) | (df[col] > upper_bound)
    return outlier_mask

def compute_heat_index(temp_c, humidity):
    """Computes Heat Index in Celsius via Steadman & Rothfusz regression."""
    t_f = temp_c * 9.0 / 5.0 + 32.0
    rh = humidity
    hi_f = 0.5 * (t_f + 61.0 + ((t_f - 68.0) * 1.2) + (rh * 0.094))
    if hi_f >= 80.0:
        hi_f = (
            -42.379 + 2.04901523 * t_f + 10.14333127 * rh
            - 0.22475541 * t_f * rh - 0.00683783 * (t_f ** 2)
            - 0.05481717 * (rh ** 2) + 0.00122874 * (t_f ** 2) * rh
            + 0.00085282 * t_f * (rh ** 2) - 0.00000199 * (t_f ** 2) * (rh ** 2)
        )
    return (hi_f - 32.0) * 5.0 / 9.0

def engineer_features(df):
    """
    Constructs ML features from raw telemetry data.
    Input df must contain: ['timestamp', 'temperature', 'humidity', 'air_quality_ppm', 'motion_detected']
    """
    df = df.copy()
    if not np.issubdtype(df['timestamp'].dtype, np.datetime64):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # 1. Temporal cyclical features
    hour = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60.0
    df['hour_sin'] = np.sin(2 * np.pi * hour / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * hour / 24.0)
    df['hour_of_day'] = df['timestamp'].dt.hour
    
    # 2. Rolling window aggregations (5 windows = 2.5 minutes)
    df['temp_rolling_mean_5'] = df['temperature'].rolling(window=5, min_periods=1).mean()
    df['temp_rolling_std_5'] = df['temperature'].rolling(window=5, min_periods=1).std().fillna(0)
    
    df['hum_rolling_mean_5'] = df['humidity'].rolling(window=5, min_periods=1).mean()
    df['hum_rolling_std_5'] = df['humidity'].rolling(window=5, min_periods=1).std().fillna(0)
    
    df['ppm_rolling_mean_5'] = df['air_quality_ppm'].rolling(window=5, min_periods=1).mean()
    df['ppm_rolling_std_5'] = df['air_quality_ppm'].rolling(window=5, min_periods=1).std().fillna(0)
    
    # 3. Rate of change (differential between current and previous window)
    df['d_temp_dt'] = df['temperature'].diff().fillna(0)
    df['d_ppm_dt'] = df['air_quality_ppm'].diff().fillna(0)
    
    # 4. Thermal Comfort / Heat Index
    df['heat_index'] = [compute_heat_index(t, h) for t, h in zip(df['temperature'], df['humidity'])]
    
    # 5. Occupancy persistence (rolling count of motion in past 10 windows = 5 mins)
    df['occupancy_persistence'] = df['motion_detected'].rolling(window=10, min_periods=1).sum()
    
    # Select final feature columns for model input
    feature_cols = [
        'temperature',
        'humidity',
        'air_quality_ppm',
        'motion_detected',
        'heat_index',
        'temp_rolling_mean_5',
        'ppm_rolling_mean_5',
        'd_temp_dt',
        'd_ppm_dt',
        'hour_sin',
        'hour_cos',
        'occupancy_persistence'
    ]
    
    return df, feature_cols
