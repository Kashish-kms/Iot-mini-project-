"""
VeilSense Synthetic Sensor Data Generator
Generates realistic, privacy-compliant 30-second aggregated room telemetry.
Simulates diurnal temperature/humidity curves, natural VOC/CO2 accumulation,
PIR occupancy bursts, and occasional sensor outliers.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

def calculate_heat_index(temp_c, humidity):
    """Computes approximate Heat Index in Celsius using Rothfusz equation."""
    t_f = temp_c * 9/5 + 32
    rh = humidity
    hi_f = (
        -42.379 + 2.04901523*t_f + 10.14333127*rh
        - 0.22475541*t_f*rh - 0.00683783*t_f**2
        - 0.05481717*rh**2 + 0.00122874*(t_f**2)*rh
        + 0.00085282*t_f*(rh**2) - 0.00000199*(t_f**2)*(rh**2)
    )
    return (hi_f - 32) * 5/9

def assign_risk_label(row):
    """
    Assigns ground truth risk category:
    0: Safe
    1: Moderate
    2: High Risk
    """
    ppm = row['air_quality_ppm']
    temp = row['temperature']
    hum = row['humidity']
    motion = row['motion_detected']

    # Severe air hazard or extreme discomfort
    if ppm >= 850 or temp >= 32.0 or temp <= 15.0 or (hum >= 75 and ppm >= 700):
        return 2 # High Risk
    
    # Moderate air stagnation or mild thermal discomfort
    if (ppm >= 500 and ppm < 850) or (hum > 65 or hum < 30) or (temp > 27.5 or temp < 18.5):
        return 1 # Moderate
    
    # Safe room condition
    return 0 # Safe

def generate_telemetry_dataset(num_days=3, interval_seconds=30, random_seed=42):
    np.random.seed(random_seed)
    total_steps = int((num_days * 24 * 3600) / interval_seconds)
    
    start_time = datetime.now() - timedelta(days=num_days)
    timestamps = [start_time + timedelta(seconds=i * interval_seconds) for i in range(total_steps)]
    
    data = []
    
    # Baseline states
    base_temp = 22.0
    base_humidity = 48.0
    base_ppm = 410.0
    consecutive_occupied = 0
    fan_on = False

    for i, ts in enumerate(timestamps):
        hour = ts.hour + ts.minute / 60.0
        
        # Diurnal diurnal temperature cycle (coolest at 5 AM, warmest at 3 PM)
        temp_cycle = 2.5 * np.sin(2 * np.pi * (hour - 9) / 24)
        
        # Occupancy simulation: high probability during 8:30-12:30 and 14:00-19:00
        is_work_hours = (8.5 <= hour <= 12.5) or (14.0 <= hour <= 19.0)
        is_evening = (19.0 < hour <= 23.0)
        
        if is_work_hours:
            occ_prob = 0.82
        elif is_evening:
            occ_prob = 0.45
        else:
            occ_prob = 0.05
            
        motion_detected = 1 if np.random.rand() < occ_prob else 0
        motion_count = np.random.randint(3, 14) if motion_detected else (1 if np.random.rand() < 0.08 else 0)
        
        if motion_detected:
            consecutive_occupied += 1
        else:
            consecutive_occupied = max(0, consecutive_occupied - 1)
            
        # Air quality dynamics: rises with occupancy duration, drops when fan is on
        # Natural infiltration / decay towards ambient 400
        ppm_change = 0.0
        if motion_detected:
            # Respiration and human metabolic VOC accumulation
            ppm_change += np.random.uniform(1.2, 3.5) * (1 + 0.05 * min(consecutive_occupied, 30))
        else:
            # Decay towards 400
            ppm_change -= 1.8 if base_ppm > 410 else 0.2
            
        # Ventilation actuation trigger
        if base_ppm > 780:
            fan_on = True
        elif base_ppm < 460:
            fan_on = False
            
        if fan_on:
            ppm_change -= 4.5 # Rapid air exchange
            
        # Rare cooking or cleaning VOC event
        if (hour >= 19.5 and hour <= 20.2) and (i % 20 == 0):
            ppm_change += np.random.uniform(45, 90)
            
        base_ppm = np.clip(base_ppm + ppm_change + np.random.normal(0, 1.2), 370, 1250)
        
        # Temperature & Humidity with slight noise
        temp = base_temp + temp_cycle + (0.8 if motion_detected else 0.0) - (1.2 if fan_on else 0.0) + np.random.normal(0, 0.15)
        humidity = base_humidity - 1.2 * temp_cycle + (1.5 if motion_detected else 0.0) + np.random.normal(0, 0.35)
        
        # Inject occasional sensor glitch/outliers (0.3% frequency)
        is_outlier = 0
        if np.random.rand() < 0.003:
            is_outlier = 1
            outlier_type = np.random.choice(['temp_high', 'temp_low', 'hum_high', 'ppm_spike'])
            if outlier_type == 'temp_high':
                temp = 75.0 # Sensor glitch
            elif outlier_type == 'temp_low':
                temp = -20.0
            elif outlier_type == 'hum_high':
                humidity = 100.0
            elif outlier_type == 'ppm_spike':
                base_ppm = 2500.0
                
        row = {
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'temperature': round(float(temp), 2),
            'humidity': round(float(humidity), 2),
            'air_quality_ppm': round(float(base_ppm), 1),
            'motion_detected': int(motion_detected),
            'motion_count': int(motion_count),
            'fan_active': int(fan_on),
            'is_outlier': int(is_outlier)
        }
        
        # Calculate risk label
        row['risk_level'] = assign_risk_label(row)
        data.append(row)
        
    df = pd.DataFrame(data)
    return df

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, '..', 'data')
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating synthetic dataset (3 days of 30s aggregate windows)...")
    df = generate_telemetry_dataset(num_days=3, interval_seconds=30)
    
    csv_path = os.path.join(output_dir, 'sample_readings.csv')
    df.to_csv(csv_path, index=False)
    print(f"Dataset successfully created at: {csv_path}")
    print(f"Total rows: {len(df)}")
    print(f"Class distribution:\n{df['risk_level'].value_counts(normalize=True).round(3)}")
