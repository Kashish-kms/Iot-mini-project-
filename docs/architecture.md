# VeilSense: 4-Layer System Architecture

```mermaid
graph TD
    subgraph "Layer 1: Edge Sensing Node (ESP32)"
        DHT[DHT22 Sensor<br/>Temp & Humidity] -->|1 Hz GPIO 4| MCU[ESP32 Microcontroller<br/>Xtensa Dual-Core 240MHz]
        MQ[MQ-135 Sensor<br/>Hazardous Gases / PPM] -->|1 Hz ADC 34| MCU
        PIR[PIR Motion Sensor<br/>Binary Occupancy] -->|Interrupt GPIO 27| MCU
        MCU -->|30s Rolling Window Buffer| AGG[On-Device Aggregator<br/>RAM Buffer]
        AGG -->|Immediate Zeroing| PURGE[Raw 1s Memories Purged]
    end

    subgraph "Layer 2: Transport Security (mTLS / MQTT)"
        AGG -->|TLS 1.3 / Port 8883<br/>X.509 Client Cert| BROKER[Eclipse Mosquitto Broker<br/>TLS Listener + Topic ACLs]
        RELAY[Ventilation Fan Relay<br/>GPIO 18] <--|Actuation Commands<br/>veilsense/actuation/fan| BROKER
    end

    subgraph "Layer 3: Cloud Preprocessing Pipeline"
        BROKER -->|veilsense/telemetry/room1| CONSUMER[Paho-MQTT Consumer<br/>FastAPI Service]
        CONSUMER --> IQR[Outlier Cleaning<br/>IQR Factor = 2.5]
        IQR --> FEAT[Feature Engineering<br/>Rolling Stats, Heat Index, Rate-of-Change]
        FEAT --> DB[(SQLite Database<br/>WAL Mode)]
    end

    subgraph "Layer 4: Machine Learning & Presentation"
        FEAT --> ML[Random Forest Classifier<br/>99.9% Test Accuracy]
        ML --> RISK[Risk Inference<br/>Safe / Moderate / High]
        RISK --> ACT[Automated Fan Actuator<br/>High PPM Trigger]
        ACT --> BROKER
        DB --> REST[FastAPI REST API<br/>JWT Auth / Endpoints]
        CONSUMER --> WS[WebSocket Hub<br/>/ws/live Streaming]
        REST --> UI[Next.js 14 App Router<br/>Glassmorphism Dashboard]
        WS --> UI
    end
```

---

## Architectural Principles
1. **Physical Privacy Guarantee**: No cameras or microphones exist on the hardware bus. Surveillance is physically impossible.
2. **Edge Aggregation**: Micro-samples are averaged on-device before transmission, defeating micro-gait or fine-grained acoustic presence fingerprinting.
3. **Defense in Depth**: Communication is protected by TLS 1.3 encryption, mutual certificate verification, role-based topic isolation, and stateless JWT tokens.
