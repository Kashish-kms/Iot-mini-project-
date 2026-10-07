"""
VeilSense ML Training Pipeline
Trains and compares:
1. Rule-Based Threshold Baseline
2. Logistic Regression (Linear)
3. Random Forest (Non-linear Ensemble)

Outputs model metrics, confusion matrix, feature importance, and persists artifacts.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import time

from features import engineer_features, detect_outliers_iqr
from generate_synthetic_data import generate_telemetry_dataset

class RuleBasedBaseline:
    """Heuristic threshold classification baseline."""
    def predict(self, X_df):
        preds = []
        for _, row in X_df.iterrows():
            ppm = row['air_quality_ppm']
            temp = row['temperature']
            hum = row['humidity']
            if ppm >= 800 or temp >= 30.0 or temp <= 16.0:
                preds.append(2) # High
            elif ppm >= 500 or hum > 65 or hum < 32 or temp > 27.0:
                preds.append(1) # Moderate
            else:
                preds.append(0) # Safe
        return np.array(preds)

def evaluate_model(name, y_true, y_pred, latency_ms=0.0):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist()
    
    return {
        'model_name': name,
        'accuracy': round(float(acc), 4),
        'precision': round(float(prec), 4),
        'recall': round(float(rec), 4),
        'f1_score': round(float(f1), 4),
        'latency_ms': round(float(latency_ms), 2),
        'confusion_matrix': cm
    }

def run_training():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, '..', 'data', 'sample_readings.csv')
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Check if dataset exists or generate it
    if not os.path.exists(data_path):
        print("Data file not found, generating fresh synthetic dataset...")
        df_raw = generate_telemetry_dataset(num_days=3, interval_seconds=30)
        df_raw.to_csv(data_path, index=False)
    else:
        df_raw = pd.read_csv(data_path)
        
    print(f"Loaded {len(df_raw)} raw samples.")
    
    # 1. Clean outliers
    outliers = detect_outliers_iqr(df_raw, factor=2.5)
    df_clean = df_raw[~outliers].copy().reset_index(drop=True)
    print(f"Removed {outliers.sum()} anomalous/glitch outlier records. Clean records: {len(df_clean)}")
    
    # 2. Feature engineering
    df_features, feature_cols = engineer_features(df_clean)
    
    X = df_features[feature_cols]
    y = df_features['risk_level'].astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    metrics_summary = {}
    
    # --- Model 1: Rule-Based Baseline ---
    t0 = time.time()
    baseline = RuleBasedBaseline()
    y_pred_base = baseline.predict(X_test)
    base_latency = (time.time() - t0) * 1000 / len(X_test)
    metrics_summary['baseline'] = evaluate_model("Rule-Based Baseline", y_test, y_pred_base, base_latency)
    
    # --- Model 2: Logistic Regression ---
    t0 = time.time()
    log_reg = LogisticRegression(max_iter=1000, random_state=42)
    log_reg.fit(X_train_scaled, y_train)
    train_time_lr = time.time() - t0
    
    t0 = time.time()
    y_pred_lr = log_reg.predict(X_test_scaled)
    lr_latency = (time.time() - t0) * 1000 / len(X_test)
    metrics_summary['logistic_regression'] = evaluate_model("Logistic Regression", y_test, y_pred_lr, lr_latency)
    
    # --- Model 3: Random Forest Classifier ---
    t0 = time.time()
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train) # Tree-based handles unscaled nicely, but can also use scaled
    train_time_rf = time.time() - t0
    
    t0 = time.time()
    y_pred_rf = rf.predict(X_test)
    rf_latency = (time.time() - t0) * 1000 / len(X_test)
    metrics_summary['random_forest'] = evaluate_model("Random Forest (Production)", y_test, y_pred_rf, rf_latency)
    
    # Feature Importances from Random Forest
    importances = rf.feature_importances_
    feat_imp = [
        {'feature': col, 'importance': round(float(imp), 4)}
        for col, imp in sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)
    ]
    
    output_report = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'dataset_size_clean': len(df_clean),
        'dataset_size_raw': len(df_raw),
        'outliers_removed': int(outliers.sum()),
        'feature_names': feature_cols,
        'feature_importance': feat_imp,
        'models': metrics_summary,
        'best_model': 'random_forest'
    }
    
    # Save artifacts
    joblib.dump(rf, os.path.join(models_dir, 'random_forest.joblib'))
    joblib.dump(log_reg, os.path.join(models_dir, 'logistic_regression.joblib'))
    joblib.dump(scaler, os.path.join(models_dir, 'scaler.joblib'))
    
    with open(os.path.join(models_dir, 'metrics.json'), 'w') as f:
        json.dump(output_report, f, indent=2)
        
    print("\n--- Model Evaluation Results ---")
    for m_key, m_val in metrics_summary.items():
        print(f"[{m_val['model_name']}] Accuracy: {m_val['accuracy']:.4f} | F1: {m_val['f1_score']:.4f} | Latency: {m_val['latency_ms']:.2f}ms")
    
    print("\nTop 5 Feature Importances:")
    for item in feat_imp[:5]:
        print(f"  {item['feature']}: {item['importance']:.4f}")
        
    print(f"\nModel artifacts saved to {models_dir}")
    return output_report

if __name__ == '__main__':
    run_training()
