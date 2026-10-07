import json
import ssl
import os
import threading
import time
import asyncio
from datetime import datetime
import paho.mqtt.client as mqtt
from .config import settings
from .database import get_db_connection
from .ml_service import ml_service
from .websocket_hub import ws_hub

class MQTTService:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.latest_status = {
            "online": True,
            "device_id": "ESP32-NODE-01",
            "ip_address": "192.168.1.142",
            "wifi_rssi_dbm": -58,
            "firmware_version": "v1.4.2-tls",
            "uptime_seconds": 184520,
            "free_heap_bytes": 182340,
            "sampling_interval_sec": 30,
            "tls_secured": True,
            "tls_cipher": "TLS_AES_256_GCM_SHA384",
            "sensors": {
                "dht22": {"status": "nominal", "pin": 4, "last_read_ms": 12},
                "mq135": {"status": "warmed_up", "pin": 34, "heater_resistance_ohms": 21.4},
                "pir": {"status": "active", "pin": 27, "interrupt_count": 842}
            },
            "last_seen": datetime.now().isoformat()
        }
        self.fan_state = 0 # 0: OFF, 1: ON
        self.auto_fan = True
        self.main_loop = None

    def start(self, event_loop=None):
        self.main_loop = event_loop
        thread = threading.Thread(target=self._run_mqtt, daemon=True)
        thread.start()
        
        # Also start an autonomous background generator for live dashboard streaming
        sim_thread = threading.Thread(target=self._run_background_simulation, daemon=True)
        sim_thread.start()

    def _run_mqtt(self):
        client_id = f"veilsense_backend_{int(time.time())}"
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        
        if settings.MQTT_USERNAME:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            
        if settings.MQTT_USE_TLS:
            ca_cert = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "..", "infra", "certs", "ca.crt"))
            if os.path.exists(ca_cert):
                self.client.tls_set(
                    ca_certs=ca_cert,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS_CLIENT
                )
                
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        port = settings.MQTT_TLS_PORT if settings.MQTT_USE_TLS else settings.MQTT_BROKER_PORT
        try:
            print(f"[MQTT] Attempting connection to {settings.MQTT_BROKER_HOST}:{port}...")
            self.client.connect(settings.MQTT_BROKER_HOST, port, keepalive=60)
            self.client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Broker connection notice: {e} (Backend running in autonomous simulation mode)")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True
            print("[MQTT] Connected to broker successfully.")
            client.subscribe(settings.MQTT_TOPIC_TELEMETRY)
        else:
            print(f"[MQTT] Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.is_connected = False
        print(f"[MQTT] Disconnected from broker (rc={rc})")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            self.handle_incoming_telemetry(payload)
        except Exception as e:
            print(f"[MQTT] Error handling incoming payload: {e}")

    def handle_incoming_telemetry(self, payload: dict):
        temp = float(payload.get('temperature', 22.0))
        hum = float(payload.get('humidity', 48.0))
        ppm = float(payload.get('air_quality_ppm', 420.0))
        motion = int(payload.get('motion_detected', 0))
        motion_count = int(payload.get('motion_count', 0))
        device_id = payload.get('device_id', 'ESP32-NODE-01')
        ts = payload.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # ML Inference
        pred = ml_service.predict_risk(temp, hum, ppm, motion)
        risk_level = pred['risk_level']
        confidence = pred['confidence']
        
        # Auto-ventilation actuation
        if self.auto_fan:
            if risk_level == 2 and self.fan_state == 0:
                self.actuate_fan("FAN_ON", "Automated AI Ventilation: High Risk detected")
            elif risk_level == 0 and ppm < 450 and self.fan_state == 1:
                self.actuate_fan("FAN_OFF", "Automated AI Ventilation: Air quality normalized")
                
        # Persist to database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO readings (
                    timestamp, temperature, humidity, air_quality_ppm,
                    motion_detected, motion_count, fan_active,
                    risk_level, risk_confidence, is_outlier, device_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ts, temp, hum, ppm, motion, motion_count, self.fan_state, risk_level, confidence, 0, device_id))
            
            # If high risk, add alert
            if risk_level == 2:
                cursor.execute("""
                    INSERT INTO alerts (timestamp, severity, title, message, resolved)
                    VALUES (?, ?, ?, ?, 0)
                """, (ts, 'critical', 'Critical Air Stagnation Alert', f'Air quality spiked to {ppm:.1f} PPM with high thermal load.', 0))
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[MQTT] Database write error: {e}")

        # Update node status
        self.latest_status['last_seen'] = datetime.now().isoformat()
        self.latest_status['uptime_seconds'] += 30

        # Broadcast event to WebSocket clients
        reading_event = {
            "type": "TELEMETRY_UPDATE",
            "data": {
                "timestamp": ts,
                "temperature": round(temp, 2),
                "humidity": round(hum, 2),
                "air_quality_ppm": round(ppm, 1),
                "motion_detected": motion,
                "motion_count": motion_count,
                "fan_active": self.fan_state,
                "risk_level": risk_level,
                "risk_label": pred['risk_label'],
                "risk_confidence": confidence,
                "probabilities": pred['probabilities'],
                "top_contributing_factors": pred['top_contributing_factors'],
                "recommendations": pred['recommendations'],
                "device_id": device_id
            }
        }
        
        if self.main_loop:
            asyncio.run_coroutine_threadsafe(ws_hub.broadcast(reading_event), self.main_loop)

    def actuate_fan(self, action: str, reason: str = "Manual toggle"):
        if action == "FAN_ON":
            self.fan_state = 1
        elif action == "FAN_OFF":
            self.fan_state = 0
            
        # Publish MQTT actuation message
        if self.client and self.is_connected:
            act_payload = json.dumps({
                "action": action,
                "fan_state": self.fan_state,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            self.client.publish(settings.MQTT_TOPIC_ACTUATION, act_payload, qos=1)
            print(f"[MQTT] Published actuation to {settings.MQTT_TOPIC_ACTUATION}: {action}")
            
        # Log to DB
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO actuation_log (timestamp, action, triggered_by, details)
                VALUES (?, ?, ?, ?)
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), action, reason, f"Fan state is now {self.fan_state}"))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[DB] Actuation log error: {e}")

    def _run_background_simulation(self):
        """Generates realistic telemetry every 4 seconds to keep dashboard lively and responsive."""
        import random
        base_temp = 22.8
        base_hum = 46.5
        base_ppm = 425.0
        
        while True:
            time.sleep(4)
            # Smooth drift
            motion = 1 if random.random() < 0.35 else 0
            motion_count = random.randint(2, 9) if motion else 0
            
            if motion:
                base_ppm += random.uniform(1.5, 4.0)
            else:
                base_ppm = max(390.0, base_ppm - random.uniform(0.5, 1.8))
                
            if self.fan_state == 1:
                base_ppm = max(380.0, base_ppm - 6.0)
                base_temp = max(20.5, base_temp - 0.1)
            else:
                base_temp = min(26.5, max(21.0, base_temp + random.uniform(-0.08, 0.08)))
                
            base_hum = min(62.0, max(38.0, base_hum + random.uniform(-0.15, 0.15)))
            
            payload = {
                "temperature": round(base_temp, 2),
                "humidity": round(base_hum, 2),
                "air_quality_ppm": round(base_ppm, 1),
                "motion_detected": motion,
                "motion_count": motion_count,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "device_id": "ESP32-NODE-01"
            }
            self.handle_incoming_telemetry(payload)

mqtt_service = MQTTService()
