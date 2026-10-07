"""
VeilSense Sensor Hardware Simulator
Simulates ESP32 node publishing 30-second aggregated telemetry over TLS MQTT (or HTTP fallback).
Sends temperature (DHT22), humidity (DHT22), air quality PPM (MQ-135), and motion activity (PIR).
"""

import time
import json
import random
import argparse
import ssl
import os
from datetime import datetime
import paho.mqtt.client as mqtt

def run_simulator():
    parser = argparse.ArgumentParser(description="VeilSense ESP32 Sensor Simulator")
    parser.add_argument("--broker", default="localhost", help="MQTT Broker host")
    parser.add_argument("--port", type=int, default=8883, help="MQTT Broker port (8883 for TLS, 1883 for plain)")
    parser.add_argument("--tls", action="store_true", default=False, help="Enable TLS connection")
    parser.add_argument("--ca-cert", default="../infra/certs/ca.crt", help="Path to CA certificate")
    parser.add_argument("--interval", type=int, default=30, help="Publish interval in seconds (default: 30)")
    parser.add_argument("--username", default="veilsense_edge", help="MQTT username")
    parser.add_argument("--password", default="edge_secret_2025", help="MQTT password")
    args = parser.parse_args()

    client = mqtt.Client(client_id="ESP32_SIMULATOR_NODE", protocol=mqtt.MQTTv311)
    if args.username:
        client.username_pw_set(args.username, args.password)

    if args.tls:
        ca_path = os.path.abspath(args.ca_cert)
        if os.path.exists(ca_path):
            print(f"[Simulator] Loading TLS CA Certificate from: {ca_path}")
            client.tls_set(ca_certs=ca_path, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
            client.tls_insecure_set(True)
        else:
            print(f"[Simulator] Warning: CA cert not found at {ca_path}. Disabling TLS verification.")

    def on_connect(c, userdata, flags, rc):
        if rc == 0:
            print(f"[Simulator] Connected to MQTT broker at {args.broker}:{args.port}")
            # Subscribe to actuation topic
            c.subscribe("veilsense/actuation/fan")
        else:
            print(f"[Simulator] MQTT Connection failed with code {rc}")

    def on_message(c, userdata, msg):
        print(f"[Simulator] Actuation message received on {msg.topic}: {msg.payload.decode('utf-8')}")

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(args.broker, args.port, keepalive=60)
        client.loop_start()
    except Exception as e:
        print(f"[Simulator] Could not connect to MQTT broker ({e}). Falling back to local demonstration mode.")

    base_temp = 22.5
    base_hum = 47.0
    base_ppm = 420.0
    window_count = 0

    print(f"\n[Simulator] Starting VeilSense ESP32 edge emulation (publishing every {args.interval}s)...")
    print("-" * 65)

    try:
        while True:
            window_count += 1
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Simulate physical drift & human presence
            motion = 1 if random.random() < 0.40 else 0
            motion_count = random.randint(3, 12) if motion else 0
            
            if motion:
                base_ppm += random.uniform(2.0, 5.0)
            else:
                base_ppm = max(390.0, base_ppm - random.uniform(0.8, 2.0))
                
            base_temp = min(27.0, max(20.5, base_temp + random.uniform(-0.1, 0.1)))
            base_hum = min(60.0, max(38.0, base_hum + random.uniform(-0.2, 0.2)))
            
            payload = {
                "timestamp": now_str,
                "device_id": "ESP32-NODE-01",
                "temperature": round(base_temp, 2),
                "humidity": round(base_hum, 2),
                "air_quality_ppm": round(base_ppm, 1),
                "motion_detected": motion,
                "motion_count": motion_count,
                "window_duration_sec": args.interval
            }
            
            topic = "veilsense/telemetry/room1"
            json_data = json.dumps(payload)
            
            try:
                client.publish(topic, json_data, qos=1)
                print(f"[{now_str}] Window #{window_count:04d} -> Temp: {base_temp:.1f}°C | Hum: {base_hum:.1f}% | MQ-135: {base_ppm:.1f} PPM | Motion: {motion}")
            except Exception as e:
                print(f"[{now_str}] Publish error: {e}")
                
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[Simulator] Stopping sensor simulation.")
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    run_simulator()
