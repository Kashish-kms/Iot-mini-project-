# VeilSense ESP32 Edge Firmware

## Hardware Specifications
- **Microcontroller**: ESP32 Dev Module (Dual-core Tensilica Xtensa 32-bit LX6 @ 240MHz, 520 KB SRAM, 4MB Flash)
- **Temperature & Humidity Sensor**: DHT22 (AM2302 capacitive digital sensor)
- **Air Quality & Hazardous Gas Sensor**: MQ-135 (metal-oxide semiconductor sensor)
- **Occupancy & Motion Sensor**: HC-SR501 or AM312 Passive Infrared (PIR)
- **Ventilation Actuator**: 5V Single-Channel Relay Module (Active HIGH)

---

## Wiring & Pinout Diagram

| Sensor / Module | Sensor Pin | ESP32 GPIO Pin | Connection Type | Operating Voltage |
| :--- | :--- | :--- | :--- | :--- |
| **DHT22** | VCC | 3.3V | Power | 3.3V |
| | DATA | **GPIO 4** | Digital I/O (10k pull-up) | 3.3V |
| | GND | GND | Ground | 0V |
| **MQ-135** | VCC | 5V / VIN | Heater Power | 5.0V |
| | AOUT | **GPIO 34** | ADC1_CH6 (Analog In) | 0 - 3.3V (voltage divider recommended) |
| | GND | GND | Ground | 0V |
| **PIR (HC-SR501)** | VCC | 5V / VIN | Power | 5.0V |
| | OUT | **GPIO 27** | Digital In (Hardware Interrupt) | 3.3V logic |
| | GND | GND | Ground | 0V |
| **Relay (Fan)** | VCC | 5V / VIN | Coil Power | 5.0V |
| | IN | **GPIO 18** | Digital Out | 3.3V logic |
| | GND | GND | Ground | 0V |

---

## Privacy By Design: Edge Aggregation Architecture
Unlike conventional smart cameras or continuous microphone feeds:
1. **Zero Acoustic & Optical Sensing**: The node physically possesses no camera lenses or microphones.
2. **On-Device Aggregation Window**: The ESP32 samples local sensors at 1 Hz, maintaining running averages in volatile memory.
3. **Transient Memory Purging**: At the end of every 30-second window, the micro-samples are mathematically reduced to statistical aggregates (mean, variance, pulse count), and raw memory buffers are zeroed out before network transmission.
4. **Encrypted Egress**: Telemetry is encapsulated in JSON and encrypted using TLS 1.3 / mTLS before leaving the physical room boundary.

---

## Flashing Instructions
1. Install **Arduino IDE** or **PlatformIO**.
2. Install the ESP32 board support package (by Espressif Systems).
3. Install required libraries via Library Manager:
   - `DHT sensor library` by Adafruit
   - `PubSubClient` by Nick O'Leary
   - `ArduinoJson` by Benoit Blanchon (v6.x)
4. Copy `config.h.example` to `config.h`:
   ```bash
   cp config.h.example config.h
   ```
5. Enter your Wi-Fi SSID, password, MQTT broker IP, and paste the Root CA Certificate.
6. Select Board **ESP32 Dev Module**, choose your COM port, and click **Upload**.
