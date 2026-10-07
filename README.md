# VeilSense: Privacy-Aware Intelligent Smart IoT Monitoring Platform

> **"Intelligence without intrusion."**

VeilSense is a production-quality, privacy-first intelligent IoT monitoring platform for ambient room climate and occupancy monitoring. By replacing optical cameras and acoustic microphones with non-intrusive ambient sensors (**DHT22**, **MQ-135**, **PIR**), VeilSense preserves personal privacy while delivering rich environmental hazard classification powered by machine learning.

---

## 1. System Architecture

```
[ ESP32 Edge Node ]
  ├── DHT22 (Temp & Humidity @ 1 Hz)
  ├── MQ-135 (Air Quality PPM @ 1 Hz)
  └── PIR (Passive Infrared Occupancy)
       │
       ▼ (On-Device 30s Window Averaging & Volatile Memory Purge)
[ TLS 1.3 / mTLS MQTT Broker ] (Port 8883, Mosquitto, X.509 Certs)
       │
       ▼ (Topic: veilsense/telemetry/room1)
[ FastAPI Cloud Ingestion Service ]
  ├── IQR Outlier Cleaning (factor = 2.5)
  ├── Feature Engineering (Rolling stats, Heat Index, Rate-of-Change)
  └── SQLite (WAL Mode High-Throughput Persistence)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
[ Machine Learning Models ]      [ Live WebSocket Hub & REST API ]
  ├── Rule-Based Baseline (92.3%)          │
  ├── Logistic Regression (98.7%)          ▼
  └── Random Forest Champion (99.9%)  [ Next.js 14 Web Application ]
                                        ├── Real-time Live Dashboard
                                        ├── Telemetry Data Explorer
                                        ├── EDA Insights Studio
                                        ├── ML Lab & What-If Simulator
                                        └── Security & Privacy Center
```

---

## 2. Monorepo Structure

```
/website
├── /frontend       # Next.js 14 App Router, TypeScript, Tailwind CSS, Lucide icons
├── /backend        # Python FastAPI, SQLite ORM, MQTT consumer, WebSocket streaming
├── /ml             # Training pipeline, synthetic data generator, model evaluation
├── /firmware       # ESP32 C++ Arduino sketch, on-device 30s aggregation buffer
├── /infra          # Mosquitto TLS config, OpenSSL certificate scripts, docker-compose
├── /data           # Sample dataset (sample_readings.csv) and data dictionary
├── /docs           # 4-layer architecture specification and STRIDE threat model
└── README.md
```

---

## 3. Quick Start Guide

### Prerequisites
- **Node.js**: v18+ (Node 24 recommended)
- **Python**: 3.10+ (Python 3.11 recommended)
- **Git**

---

### Step 1: Backend Setup & Launch
Open a terminal in the repository root:
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server (runs on http://localhost:8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Note: The backend automatically initializes SQLite `veilsense.db` and seeds 8,640 records from `data/sample_readings.csv` upon first boot.*

---

### Step 2: Frontend Setup & Launch
Open a second terminal:
```bash
# Navigate to frontend
cd frontend

# Install dependencies (if not already installed)
npm install

# Start Next.js development server (runs on http://localhost:3000)
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser!

---

### Step 3: Run the Sensor Hardware Simulator (Optional)
To stream live telemetry over MQTT or autonomous simulation loops:
```bash
cd backend
python simulate_sensors.py --interval 5
```

---

### Step 4: Docker Compose Orchestration (Optional)
To run the complete production stack (Mosquitto TLS broker + FastAPI + Next.js):
```bash
cd infra
docker-compose up --build
```

---

## 4. Machine Learning Benchmarks

VeilSense trains and benchmarks three distinct models on 8,617 clean 30-second telemetry windows:

| Model Architecture | Accuracy | Weighted Precision | Weighted Recall | F1 Score | Inference Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Rule-Based Baseline** | 92.29% | 92.21% | 92.29% | 92.21% | 0.05 ms |
| **Logistic Regression** | 98.72% | 98.72% | 98.72% | 98.72% | 0.01 ms |
| **Random Forest (Production)** | **99.94%** | **99.94%** | **99.94%** | **99.94%** | **0.03 ms** |

### Top Predictive Features (MDI Gini Importance):
1. `air_quality_ppm` (44.9%)
2. `ppm_rolling_mean_5` (33.2%)
3. `temp_rolling_mean_5` (4.9%)
4. `occupancy_persistence` (4.6%)
5. `hour_sin` (3.2%)

---

## 5. Security & Privacy Highlights

- **Zero Optical/Audio Intrusion**: Hardware contains no lenses or microphones.
- **On-Device 30s Aggregation**: High-frequency micro-biometrics are discarded in volatile memory.
- **TLS 1.3 / mTLS Transport**: All edge packets are encrypted with AES-256-GCM.
- **Seeded Demo Credentials**:
  - Email: `demo@veilsense.io`
  - Password: `veilsense2025`
