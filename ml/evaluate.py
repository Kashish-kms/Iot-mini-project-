"""
VeilSense Exploratory Data Analysis (EDA) & Metrics Exporter
Computes correlation matrices, diurnal patterns, distribution histograms,
and summary statistics for the /insights EDA dashboard.
"""

import os
import json
import numpy as np
import pandas as pd

def generate_eda_summary(csv_path=None):
    if csv_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, '..', 'data', 'sample_readings.csv')
        
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 1. Distribution summary
    stats = {
        'temperature': {
            'min': round(float(df['temperature'].min()), 2),
            'max': round(float(df['temperature'].max()), 2),
            'mean': round(float(df['temperature'].mean()), 2),
            'std': round(float(df['temperature'].std()), 2)
        },
        'humidity': {
            'min': round(float(df['humidity'].min()), 2),
            'max': round(float(df['humidity'].max()), 2),
            'mean': round(float(df['humidity'].mean()), 2),
            'std': round(float(df['humidity'].std()), 2)
        },
        'air_quality_ppm': {
            'min': round(float(df['air_quality_ppm'].min()), 2),
            'max': round(float(df['air_quality_ppm'].max()), 2),
            'mean': round(float(df['air_quality_ppm'].mean()), 2),
            'std': round(float(df['air_quality_ppm'].std()), 2)
        },
        'total_samples': len(df),
        'outlier_count': int(df['is_outlier'].sum()) if 'is_outlier' in df.columns else 0
    }
    
    # 2. Correlation matrix (numeric cols)
    num_cols = ['temperature', 'humidity', 'air_quality_ppm', 'motion_detected', 'risk_level']
    corr_df = df[num_cols].corr().round(3)
    correlation_matrix = {
        'columns': num_cols,
        'values': corr_df.values.tolist()
    }
    
    # 3. Hourly diurnal pattern (0-23 hours)
    df['hour'] = df['timestamp'].dt.hour
    hourly = df.groupby('hour').agg({
        'temperature': 'mean',
        'humidity': 'mean',
        'air_quality_ppm': 'mean',
        'motion_detected': 'mean'
    }).round(2).reset_index()
    
    hourly_patterns = hourly.to_dict(orient='records')
    
    # 4. Class label distribution
    label_counts = df['risk_level'].value_counts().to_dict()
    label_dist = [
        {'label': 'Safe', 'value': int(label_counts.get(0, 0)), 'percentage': round(label_counts.get(0, 0) / len(df) * 100, 1)},
        {'label': 'Moderate', 'value': int(label_counts.get(1, 0)), 'percentage': round(label_counts.get(1, 0) / len(df) * 100, 1)},
        {'label': 'High Risk', 'value': int(label_counts.get(2, 0)), 'percentage': round(label_counts.get(2, 0) / len(df) * 100, 1)}
    ]
    
    # 5. Histogram bins for temperature, humidity, air quality
    histograms = {}
    for col, bins in [('temperature', 10), ('humidity', 10), ('air_quality_ppm', 10)]:
        counts, bin_edges = np.histogram(df[col].dropna(), bins=bins)
        histograms[col] = [
            {'range': f"{round(bin_edges[i], 1)}-{round(bin_edges[i+1], 1)}", 'count': int(counts[i])}
            for i in range(len(counts))
        ]
        
    eda_data = {
        'statistics': stats,
        'correlation_matrix': correlation_matrix,
        'hourly_patterns': hourly_patterns,
        'label_distribution': label_dist,
        'histograms': histograms
    }
    return eda_data

if __name__ == '__main__':
    eda = generate_eda_summary()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, 'models', 'eda_summary.json'), 'w') as f:
        json.dump(eda, f, indent=2)
    print("EDA summary exported successfully to ml/models/eda_summary.json")
