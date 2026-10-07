# VeilSense Security Threat Model & STRIDE Analysis

## 1. System Overview & Trust Boundaries
VeilSense monitors single-room environmental air quality and human presence using non-intrusive sensors (DHT22, MQ-135, PIR).

### Trust Boundaries:
- **Boundary 1: Edge Sensing Node to Local Network**: Between the ESP32 physical microcontroller and the Wi-Fi access point.
- **Boundary 2: Transport to Broker**: Over TCP/IP to the Mosquitto MQTT broker.
- **Boundary 3: Cloud / Server Ingestion**: Between the MQTT broker, FastAPI service, and SQLite database.
- **Boundary 4: User Interface**: Between web client browsers and the FastAPI REST/WebSocket endpoints.

---

## 2. STRIDE Threat Assessment

| Threat Category | Potential Threat Vector | VeilSense Countermeasure | Mitigation Status |
| :--- | :--- | :--- | :--- |
| **Spoofing (Identity)** | Adversary impersonating ESP32 to inject fabricated sensor readings. | Mutual TLS (mTLS) with unique X.509 client certificates and password auth. | **Mitigated** |
| **Tampering (Data)** | Attacker altering temperature, gas PPM, or actuation commands in transit. | TLS 1.3 AES-256-GCM cipher suite guaranteeing cryptographic integrity. | **Mitigated** |
| **Repudiation** | Client or device denying transmission of actuation command. | Monotonically timestamped SQLite actuation audit log (`actuation_log`). | **Mitigated** |
| **Information Disclosure** | Eavesdropper sniffing sensor feeds or inferring room occupancy. | Zero optical/audio sensing; 30s edge aggregation; encrypted TLS pipe. | **Mitigated** |
| **Denial of Service** | Flooding broker or API with high-frequency MQTT traffic. | Rate limiting, strict connection keep-alives, and QoS 1 message buffering. | **Mitigated** |
| **Elevation of Privilege** | Normal user attempting unauthorized administrative actuation. | Role-Based Access Control (RBAC) enforced via stateless HS256 JWT claims. | **Mitigated** |

---

## 3. Explicit Boundaries: In-Scope vs. Out-of-Scope

### In-Scope (Strictly Defended):
- Eavesdropping on Wi-Fi packets.
- Unauthorized MQTT broker connection attempts.
- Replay attacks on historical sensor readings.
- Identity profiling via occupancy micro-bursts.

### Out-of-Scope (Documented Assumptions):
- Physical hardware theft or disassembly of the ESP32 node.
- Direct physical probing of GPIO traces with oscilloscopes.
- Physical occlusion of sensor orifices (e.g. taping the MQ-135 chamber).
- Root-level compromise of the host server operating system.
