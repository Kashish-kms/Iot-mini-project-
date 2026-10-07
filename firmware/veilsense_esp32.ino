/*
 * ==============================================================================
 * VeilSense: Privacy-Aware Intelligent Edge Monitoring Firmware
 * Target: ESP32 Dev Module / ESP-WROOM-32
 *
 * Sensors:
 *   - DHT22 (Digital Pin 4): Ambient temperature and relative humidity
 *   - MQ-135 (ADC Pin 34): Air quality / hazardous gas detection (PPM)
 *   - PIR (Digital Pin 27): Passive Infrared binary occupancy sensor
 *
 * Privacy By Design:
 *   - Performs on-device aggregation over 30-second windows.
 *   - Discards raw 1-second samples immediately after accumulating.
 *   - Zero audio, zero video, zero biometric identification data.
 *   - Encrypts all communications via TLS 1.3/1.2 over authenticated MQTT.
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// Include credentials and configuration
#if __has_include("config.h")
  #include "config.h"
#else
  #include "config.h.example"
#endif

// Sensor instances
DHT dht(DHT_PIN, DHT_TYPE);
WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);

// PIR Interrupt State
volatile unsigned long pirTriggerCount = 0;
volatile bool motionDetectedInWindow = false;

void IRAM_ATTR handlePirInterrupt() {
  pirTriggerCount++;
  motionDetectedInWindow = true;
}

// Window Accumulators (30-second aggregation buffer)
float tempAccumulator = 0.0;
float humAccumulator = 0.0;
float ppmAccumulator = 0.0;
int sampleCountInWindow = 0;

unsigned long lastSampleTime = 0;
unsigned long windowStartTime = 0;

// MQ-135 Calibration Constants
const float V_IN = 3.3;
const float R_LOAD = 10.0; // 10k ohm load resistor
const float R_ZERO = 76.63; // Calibrated sensor resistance in clean air
const float PARA = 116.6020682;
const float PARB = 2.769034857;

float calculateMQ135PPM(int adcValue) {
  if (adcValue <= 0) return 400.0;
  float vOut = (adcValue / 4095.0) * V_IN;
  if (vOut >= V_IN) vOut = V_IN - 0.01;
  float rSensor = ((V_IN - vOut) / vOut) * R_LOAD;
  float ratio = rSensor / R_ZERO;
  float ppm = PARA * pow(ratio, -PARB);
  return constrain(ppm, 350.0, 3000.0);
}

void connectWiFi() {
  Serial.print("[WiFi] Connecting to: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[WiFi] Connected! IP: " + WiFi.localIP().toString());
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.print("[MQTT] Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(" | Payload: ");
  Serial.println(message);

  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, message);
  if (!error) {
    const char* action = doc["action"];
    if (String(action) == "FAN_ON") {
      digitalWrite(RELAY_FAN_PIN, HIGH);
      Serial.println("[Actuation] Relay Activated: Ventilation FAN ON");
    } else if (String(action) == "FAN_OFF") {
      digitalWrite(RELAY_FAN_PIN, LOW);
      Serial.println("[Actuation] Relay Deactivated: Ventilation FAN OFF");
    }
  }
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("[MQTT] Connecting over TLS to broker: ");
    Serial.println(MQTT_BROKER_HOST);

    if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("[MQTT] TLS Connection established.");
      mqttClient.subscribe(MQTT_TOPIC_ACTUATION);
      Serial.print("[MQTT] Subscribed to actuation topic: ");
      Serial.println(MQTT_TOPIC_ACTUATION);
    } else {
      Serial.print("[MQTT] Connection failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(". Retrying in 5 seconds...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n==============================================");
  Serial.println("  VeilSense ESP32 Edge Node Initializing...  ");
  Serial.println("  Privacy-Aware IoT Intelligence Platform     ");
  Serial.println("==============================================");

  // Pin Modes
  pinMode(PIR_PIN, INPUT_PULLDOWN);
  attachInterrupt(digitalPinToInterrupt(PIR_PIN), handlePirInterrupt, RISING);
  pinMode(RELAY_FAN_PIN, OUTPUT);
  digitalWrite(RELAY_FAN_PIN, LOW);
  analogReadResolution(12);

  // Start Sensors
  dht.begin();
  Serial.println("[Hardware] Sensors initialized (DHT22, MQ-135, PIR).");

  // Networking & TLS
  connectWiFi();
  espClient.setCACert(ROOT_CA_CERT);
  mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
  mqttClient.setCallback(mqttCallback);

  windowStartTime = millis();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }
  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.loop();

  unsigned long currentMillis = millis();

  // 1. High-frequency 1-second raw sampling into local memory
  if (currentMillis - lastSampleTime >= SAMPLING_PERIOD_MS) {
    lastSampleTime = currentMillis;

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int mqRaw = analogRead(MQ135_PIN);
    float ppm = calculateMQ135PPM(mqRaw);

    // Validate sensor read bounds
    if (!isnan(t) && !isnan(h)) {
      tempAccumulator += t;
      humAccumulator += h;
      ppmAccumulator += ppm;
      sampleCountInWindow++;
    }
  }

  // 2. 30-Second Window Aggregation & Privacy-Preserving Transmission
  if (currentMillis - windowStartTime >= WINDOW_DURATION_MS) {
    if (sampleCountInWindow > 0) {
      float avgTemp = tempAccumulator / sampleCountInWindow;
      float avgHum = humAccumulator / sampleCountInWindow;
      float avgPPM = ppmAccumulator / sampleCountInWindow;

      // Construct aggregate JSON packet
      StaticJsonDocument<384> doc;
      doc["device_id"] = MQTT_CLIENT_ID;
      doc["temperature"] = round(avgTemp * 100.0) / 100.0;
      doc["humidity"] = round(avgHum * 100.0) / 100.0;
      doc["air_quality_ppm"] = round(avgPPM * 10.0) / 10.0;
      doc["motion_detected"] = motionDetectedInWindow ? 1 : 0;
      doc["motion_count"] = pirTriggerCount;
      doc["window_duration_sec"] = 30;
      doc["uptime_sec"] = millis() / 1000;
      doc["rssi"] = WiFi.RSSI();

      char jsonBuffer[512];
      serializeJson(doc, jsonBuffer);

      Serial.println("\n[Privacy Aggregation Complete] Transmitting window statistics:");
      Serial.println(jsonBuffer);

      // Publish to TLS MQTT
      mqttClient.publish(MQTT_TOPIC_TELEMETRY, jsonBuffer, true);
    }

    // Reset Aggregators (Zero raw memory retention)
    tempAccumulator = 0.0;
    humAccumulator = 0.0;
    ppmAccumulator = 0.0;
    sampleCountInWindow = 0;
    motionDetectedInWindow = false;
    pirTriggerCount = 0;
    windowStartTime = currentMillis;
  }
}
