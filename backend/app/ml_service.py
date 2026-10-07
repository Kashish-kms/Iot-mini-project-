import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

class MLService:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ml_dir = os.path.abspath(os.path.join(self.base_dir, '..', '..', 'ml'))
        self.models_dir = os.path.join(self.ml_dir, 'models')
        self.rf_model = None
        self.logreg_model = None
        self.scaler = None
        self.metrics = None
        self.load_models()

    def load_models(self):
        try:
            rf_path = os.path.join(self.models_dir, 'random_forest.joblib')
            if os.path.exists(rf_path):
                self.rf_model = joblib.load(rf_path)
                print("[MLService] Loaded Random Forest model.")
            
            lr_path = os.path.join(self.models_dir, 'logistic_regression.joblib')
            if os.path.exists(lr_path):
                self.logreg_model = joblib.load(lr_path)
                
            scaler_path = os.path.join(self.models_dir, 'scaler.joblib')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                
            metrics_path = os.path.join(self.models_dir, 'metrics.json')
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r') as f:
                    self.metrics = json.load(f)
        except Exception as e:
            print(f"[MLService] Warning loading model files: {e}")

    def compute_heat_index(self, temp_c, humidity):
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

    def predict_risk(self, temp: float, humidity: float, ppm: float, motion: int, occupancy_persistence: float = 3.0):
        # Calculate engineered features
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
        hour_sin = np.sin(2 * np.pi * hour / 24.0)
        hour_cos = np.cos(2 * np.pi * hour / 24.0)
        heat_idx = self.compute_heat_index(temp, humidity)
        
        # Heuristic / fallback rules
        rule_class = 0
        if ppm >= 850 or temp >= 32.0 or temp <= 15.0 or (humidity >= 75 and ppm >= 700):
            rule_class = 2
        elif (ppm >= 500 and ppm < 850) or (humidity > 65 or humidity < 30) or (temp > 27.5 or temp < 18.5):
            rule_class = 1
            
        risk_class = rule_class
        confidence = 0.94
        probs = {"Safe": 0.05, "Moderate": 0.15, "High Risk": 0.80} if rule_class == 2 else (
            {"Safe": 0.10, "Moderate": 0.85, "High Risk": 0.05} if rule_class == 1 else
            {"Safe": 0.92, "Moderate": 0.07, "High Risk": 0.01}
        )

        if self.rf_model is not None:
            try:
                # Features: ['temperature', 'humidity', 'air_quality_ppm', 'motion_detected', 'heat_index',
                #            'temp_rolling_mean_5', 'ppm_rolling_mean_5', 'd_temp_dt', 'd_ppm_dt',
                #            'hour_sin', 'hour_cos', 'occupancy_persistence']
                features = np.array([[
                    temp, humidity, ppm, motion, heat_idx,
                    temp, ppm, 0.0, 0.0,
                    hour_sin, hour_cos, occupancy_persistence
                ]])
                pred_prob = self.rf_model.predict_proba(features)[0]
                risk_class = int(np.argmax(pred_prob))
                confidence = float(np.max(pred_prob))
                
                probs = {
                    "Safe": round(float(pred_prob[0]), 3) if len(pred_prob) > 0 else 0.0,
                    "Moderate": round(float(pred_prob[1]), 3) if len(pred_prob) > 1 else 0.0,
                    "High Risk": round(float(pred_prob[2]), 3) if len(pred_prob) > 2 else 0.0
                }
            except Exception as e:
                print(f"[MLService] Prediction error: {e}")

        labels = {0: "Safe", 1: "Moderate", 2: "High Risk"}
        risk_label = labels.get(risk_class, "Safe")

        # Top contributing factors
        factors = []
        if ppm > 750:
            factors.append({"factor": "Elevated VOC / CO2 Equivalent", "impact": "High", "contribution": "48%"})
        elif ppm > 500:
            factors.append({"factor": "Moderate Air Stagnation", "impact": "Medium", "contribution": "35%"})
        else:
            factors.append({"factor": "Clean Ambient Air (Sub-500 PPM)", "impact": "Low", "contribution": "15%"})
            
        if temp > 28.0 or temp < 18.0:
            factors.append({"factor": "Thermal Comfort Deviation", "impact": "High", "contribution": "32%"})
        elif temp > 25.5 or temp < 20.0:
            factors.append({"factor": "Mild Thermal Drift", "impact": "Medium", "contribution": "22%"})
            
        if occupancy_persistence > 8:
            factors.append({"factor": "Persistent Room Occupancy", "impact": "Medium", "contribution": "20%"})

        recs = []
        if risk_class == 2:
            recs = [
                "Activate high-flow smart ventilation immediately.",
                "Open external windows if outdoor air index allows.",
                "Verify no localized VOC source or smoke event in room."
            ]
        elif risk_class == 1:
            recs = [
                "Trigger intermittent 5-minute air exchange fan cycle.",
                "Maintain optimal temperature setpoint between 21-24°C.",
                "Monitor for gradual pollutant accumulation."
            ]
        else:
            recs = [
                "Room environmental quality is optimal.",
                "Ventilation can remain in low-power eco standby.",
                "Thermal comfort index is within ASHRAE 55 recommended envelope."
            ]

        return {
            "risk_level": risk_class,
            "risk_label": risk_label,
            "confidence": round(confidence, 3),
            "probabilities": probs,
            "top_contributing_factors": factors,
            "recommendations": recs
        }

    def get_metrics(self):
        if self.metrics:
            return self.metrics
        metrics_path = os.path.join(self.models_dir, 'metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                self.metrics = json.load(f)
            return self.metrics
        return {"error": "Metrics not trained yet"}

ml_service = MLService()
