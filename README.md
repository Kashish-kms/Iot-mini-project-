# Privacy-Aware Intelligent Smart IoT (AIoT) — Software-Only Simulator

A **fully functional, end-to-end, privacy-aware smart IoT pipeline** where
**everything is simulated in pure Python**. No physical hardware, firmware,
cameras, audio, wiring, or identity data anywhere in the stack.

```
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│  simulator/        │     │  broker/           │     │  ingestion/        │
│                    │     │                    │     │                    │
│  SensorGenerator   │────▶│  Mosquitto :8883   │────▶│  MQTT subscriber   │
│  (T,H,CO2,motion)  │ TLS │  (TLS + auth+ACL)  │ TLS │  → SQLite telemetry│
│  (1-min AGG only)  │     │                    │     │  → features table  │
│                    │     │                    │     │                    │
└────────────────────┘     └────────────────────┘     └────────┬───────────┘
                                                              │ shared volume
                                                              ▼
                    ┌──────────────────────────┐    ┌────────────────────┐
                    │  dashboard/              │    │  ml/               │
                    │  Streamlit :8501         │    │                    │
                    │  • live gauges           │    │  train.py          │
                    │  • rolling time-series   │    │  evaluate.py       │
                    │  • RF risk prediction    │    │  (Rule vs RF, seed │
                    │  • SIMULATED actuation log│   │   split by scen.)  │
                    └──────────────────────────┘    └────────────────────┘
```

## TL;DR quick start

```bash
# 1) Generate TLS material once (script is idempotent — regenerates on each run).
cd prototype
bash broker/certs/generate_certs.sh   # WSL / Git Bash / Linux / macOS

# (Windows with OpenSSL & no bash: run broker/certs/generate_certs.sh through
#  Git-Bash, or the PowerShell equivalent in ./broker/certs/PS-Win-GenerateCerts.ps1
#  if provided; otherwise OpenSSL commands are identical to what the script runs.)

# 2) Build + run everything (Mosquitto password file is generated at build time
#    using dev defaults from .env; for production, override build args or mount
#    your own hashed passwd).
docker compose up --build

# 3) Open dashboard
start http://localhost:8501    # on Windows
# or: open http://localhost:8501 in your browser.
```

After ~30 seconds the first telemetry windows appear, after ~1-2 minutes the
preprocessing worker populates the `features` table and the ML dashboard
starts showing risk predictions.

## Project layout

```
prototype/
├── docker-compose.yml         # Orchestrates broker / simulator / ingestion / dashboard
├── requirements.txt           # Combined pip freeze for running locally without Docker
├── README.md                  # This file
├── .env                       # Shared MQTT credentials + DB paths (secrets)
│
├── simulator/
│   ├── Dockerfile
│   ├── config.py              # Tunable constants with docstrings (ASHRAE ranges noted)
│   ├── generator.py           # SensorGenerator: sinusoid + drift + occupancy state machine
│   ├── publisher.py           # MQTT TLS client (auth, reconnect, 1-min AGG publishing)
│   └── requirements.txt
│
├── broker/
│   ├── Dockerfile
│   ├── mosquitto.conf         # TLS 8883, anon=false, passwd + ACL files
│   ├── passwd                 # Placeholder; comment explains mosquitto_passwd usage
│   ├── acl                    # sim_user=write-only, ingest_user=read-only on home/room1/telemetry
│   └── certs/
│       └── generate_certs.sh  # Self-signed CA + SAN-bearing server cert (OpenSSL)
│
├── ingestion/
│   ├── Dockerfile
│   ├── database.py            # SQLite schema (telemetry/predictions/features/actuation_log)
│   ├── preprocessing.py       # IQR outlier clipping, 1-min resample, rolling + rate features
│   ├── service.py             # MQTT subscriber + writer + periodic preprocessing
│   └── requirements.txt
│
├── ml/
│   ├── train.py               # Label rules → RuleBasedClassifier + RandomForest → .joblib
│   ├── evaluate.py            # Scenario-seed split, accuracy/F1, comparison table
│   ├── models/                # Saved .joblib artifacts (created by train.py)
│   └── requirements.txt
│
├── dashboard/
│   ├── Dockerfile
│   ├── app.py                 # Streamlit app (gauges, chart, risk, actuation log)
│   ├── components.py          # Reusable Plotly gauges/charts (no Streamlit UI code)
│   └── requirements.txt
│
└── data/                      # Host-visible shared SQLite volume (iot.db + WAL files)
```

## Architecture & data flow

1. **simulator/generator.py** internally samples temperature, humidity, CO2,
   and motion every 5 s (`SAMPLING_INTERVAL_SEC`), but **never returns these
   raw samples**. It buffers them and returns exactly one aggregated summary
   (mean temperature, mean humidity, mean CO2, max motion) every
   `AGGREGATION_WINDOW_SEC` (default 60 s). This on-simulator aggregation is
   the project's **data-minimization privacy primitive** — the exact
   equivalent of running the same aggregation on an ESP32 microcontroller
   *before* publishing. No high-frequency motion pattern that could
   fingerprint room occupancy ever leaves the edge simulator.
2. **simulator/publisher.py** sends each aggregated window to
   `home/room1/telemetry` over **TLS port 8883** with username/password auth.
3. **broker** (Eclipse Mosquitto) enforces:
   - no anonymous connects,
   - per-user topic ACL: `sim_user` may **only publish** to the telemetry
     topic, `ingest_user` may **only subscribe** to it,
   - server cert signed by a local CA,
   - no plain-text listener on 1883.
4. **ingestion/service.py** validates each MQTT payload against the
   ESP32-drop-in schema and writes to `telemetry`. A background thread runs
   the preprocessing pipeline every ~2 minutes:
   - hard-clips and IQR-clips numeric outliers,
   - re-samples onto an exact 1-minute cadence with linear gap interpolation,
   - engineers features (rolling mean/std at 5- and 15-window lookbacks,
     rate-of-change per minute, hour-of-day, `is_daytime` flag) into the
     `features` table.
5. **ml/train.py** loads `features`, derives 3-class ground-truth labels
   from the known simulator physics (`low` / `medium` / `high`), trains a
   `RuleBasedClassifier` baseline and a `RandomForestClassifier`, and saves
   both with joblib metadata to `ml/models/`.
6. **ml/evaluate.py** re-splits the dataset by **scenario seed groups**
   (never row-level shuffle), retrains on the split, prints accuracy + F1
   for both models, and reports confusion matrices. A seed-based split
   exercises generalization to unseen occupancy patterns rather than
   memorization of 1-minute windows drawn from the same scenario time-series.
7. **dashboard/app.py** refreshes every ~10 s from `iot.db`, shows 4 Plotly
   gauges (T/H/CO2/motion), a dual-axis rolling time-series with
   motion-shaded regions and risk markers, a `low`/`medium`/`high` risk
   badge backed by the latest RandomForest prediction, and a
   **SIMULATED actuation log**. On HIGH-risk transitions or sustained HIGH
   reads it appends events like `VENTILATION_ON` / `HVAC_COOL_ON` /
   `VENTILATION_OFF` to the SQLite `actuation_log` table. Nothing physical
   is ever actuated.

## ESP32 drop-in compatibility

The MQTT topic `home/room1/telemetry` and JSON payload schema are **deliberately
identical** to what a real ESP32 + DHT22 + MQ-135 + PIR would publish after
on-chip 1-minute aggregation:

```json
{
  "timestamp":   1700000060000,
  "temperature": 22.34,
  "humidity":    45.12,
  "co2":         847,
  "motion":      1,
  "room_id":     "room1"
}
```

Field types match realistic ESP32 code paths: `timestamp` as epoch ms
(`uint64_t`), `co2` rounded to integer ppm (typical MQ-135/SCD4x output),
`motion` as 0/1 latching PIR (max-over-window), `temperature`/`humidity` as
floats, `room_id` as a short ASCII identifier. Broker, ingestion, ML, and
dashboard code require **zero changes** to accept future messages from a
real device publishing this exact format on the same topic.

## Training and evaluating the ML models

### Option A — inside the running dashboard container (preferred)

```bash
# Train on features already accumulated in the shared SQLite DB.
docker compose exec dashboard python /app/ml/train.py

# Evaluate (seed-based scenario split, NO row shuffle).
docker compose exec dashboard python /app/ml/evaluate.py
```

### Option B — outside Docker, on host, against the same `data/iot.db`

```bash
cd prototype
pip install -r requirements.txt
python -m ml.train
python -m ml.evaluate
```

### Option C — fully offline, no running stack

Use the built-in synthetic fallback. `train.py` and `evaluate.py` fall back
to generating ~6 weeks of synthetic 1-minute sensor data across six distinct
`SCENARIO_SEED` values, then train and evaluate on that:

```bash
cd prototype
python -m ml.train --synthetic
python -m ml.evaluate --synthetic
```

Expected stdout summary from evaluate:

```
================================================================
Model comparison (TEST set, scenario-split, no row shuffle):
================================================================
              Accuracy  F1-macro  F1-weighted
Model
RuleBased       X.XXX      X.XXX         X.XXX
RandomForest    Y.YYY      Y.YYY         Y.YYY
================================================================
```

The RandomForest typically achieves F1 ≥ 0.9 with enough scenario diversity.

## Privacy & security design

Every layer is explicitly engineered for privacy-by-design:

| Layer | Mechanism | Rationale |
|-------|-----------|-----------|
| **simulator** (edge) | On-simulator 1-minute aggregation before publish; raw 5 s samples never serialized or logged. | High-frequency motion/temp patterns can fingerprint presence and sleep schedule. Aggregating to 1-minute means destroys that granularity while preserving the bulk air-quality signal needed for IAQ control. |
| **transport** | Mandatory TLS 1.2+ on port 8883, CA-signed broker cert, no plain-text listener. | Prevents passive eavesdropping on telemetry between edge and cloud. |
| **broker auth** | Username/password over hashed Mosquitto passwd file; anonymous connections explicitly rejected. | Blocks trivial unauthorized pub/sub. |
| **broker ACL** | Least-privilege per user: simulator may only WRITE to its room topic, ingestion may only READ. | A compromised simulator cannot subscribe to others' data. A compromised ingestion cannot spoof sensor values back onto the bus. |
| **application** | No cameras, no audio, no identity data, no names/emails/phone numbers. Only four numeric channels + room identifier. | Reduces the data inventory; there is simply nothing in the dataset worth stealing or leaking. |
| **dashboard** | Simulated actuation only; dashboard has no write path back to the broker or to any GPIO. | Eliminates the most dangerous class of IoT vulnerabilities (remote physical actuation) entirely. |

## Simulation vs. real hardware — trade-offs

| Aspect | Software simulator | Physical ESP32 + sensors |
|--------|--------------------|---------------------------|
| **Cost** | $0 | ~$20 + wiring + power supply + sensor enclosures |
| **Reproducibility** | Perfect — `RANDOM_SEED`/`SCENARIO_SEED` give byte-identical runs; seed-based ML splits work out of the box. | Hard — sensors drift, batteries die, radio drops packets, HVAC schedules change between runs. |
| **Time acceleration** | Trivial (1-min window = instant via SIM_REALTIME=0); can generate months of data in seconds. | Real-time only. 1 week of data = 7 days of wall-clock runtime. |
| **Sensor realism** | Synthetic physics; no real dust buildup, long-term MQ-135 drift, direct-sun PIR false-positives, DHT22 self-heating errors, or loose wiring. | Exact distribution of real-world sensor noise, plus all failure modes you get in the field. |
| **Network failure modes** | None simulated by default (add your own TCP proxy). | WiFi drops, MQTT reconnect storms, SSL handshake failures when the clock is wrong after deep-sleep. |
| **Edge compute constraints** | None — simulator runs on server-grade x86 RAM/CPU. Would need rewriting for an 8-bit AVR or ESP8266. | Aggregation + feature math are the same, but memory/CPU for on-device ML are severely constrained. |
| **ESP32 drop-in path** | Broker, ingestion, ML, and dashboard are **100 % reusable**. Only the publisher/sensor layer changes. | — |

Bottom line: this simulator is perfect for **validating the data pipeline,
cloud/ingestion architecture, privacy controls, ML approach, and dashboard UX
before any hardware is ordered**. When physical sensors arrive, swap the
simulator service for an MQTT client running on the ESP32 and the rest of the
stack requires zero edits.

## Troubleshooting

| Symptom | Likely fix |
|---------|------------|
| Dashboard shows "No telemetry yet" for >1 min. | Check `docker compose logs simulator` for TLS auth errors → make sure `broker/certs/ca.crt` exists on host AND all 3 client containers mount it. |
| Mosquitto log says "bad username or password" for `sim_user`. | Either `.env` was changed after the image was built (rerun `docker compose build broker --no-cache`) or you mounted a stale `passwd` file from host. |
| "No predictions yet" badge for >2 min. | `ml/models/random_forest_v1.joblib` must exist. Run `docker compose exec dashboard python /app/ml/train.py` once. |
| SQLite "database is locked" errors. | Ingestion and dashboard share the same DB with WAL mode on; this is transient. If persistent, check both containers have `./data:/data:rw` and a single filesystem (not NFS). |
| `generate_certs.sh` on Windows complains about "line endings" or "no such file or directory". | Run in WSL or Git Bash; or recreate manually using the exact OpenSSL lines in the script. |

## License / ethics

This project intentionally excludes cameras, microphones, identity data, and
real physical actuation. When deploying a derivative system with real devices,
follow local privacy law (GDPR, CCPA, PIPL, etc.): disclose sensor locations
to occupants, offer opt-out, and keep the same on-edge aggregation + TLS +
ACL controls wired in here.
