import sqlite3
import os
import json
import hashlib
import pandas as pd
from datetime import datetime
from .config import settings

def get_db_connection():
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def hash_password(password: str) -> str:
    # PBKDF2 HMAC SHA-256 with fixed salt for demo
    salt = b"veilsense_salt_2025"
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Readings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        air_quality_ppm REAL NOT NULL,
        motion_detected INTEGER NOT NULL,
        motion_count INTEGER DEFAULT 0,
        fan_active INTEGER DEFAULT 0,
        risk_level INTEGER DEFAULT 0,
        risk_confidence REAL DEFAULT 0.95,
        is_outlier INTEGER DEFAULT 0,
        device_id TEXT DEFAULT 'ESP32-NODE-01'
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings (timestamp);")
    
    # 2. Alerts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        severity TEXT NOT NULL, -- 'info', 'warning', 'critical'
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        resolved INTEGER DEFAULT 0
    );
    """)
    
    # 3. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'admin'
    );
    """)
    
    # 4. Actuation Log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS actuation_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL, -- 'FAN_ON', 'FAN_OFF'
        triggered_by TEXT NOT NULL, -- 'AI_AUTOMATION', 'MANUAL_USER'
        details TEXT
    );
    """)
    
    # Check if demo user exists
    cursor.execute("SELECT id FROM users WHERE email = 'demo@veilsense.io'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            ("demo@veilsense.io", hash_password("veilsense2025"), "Research Demo User", "admin")
        )
        print("[DB] Created seeded demo user: demo@veilsense.io / veilsense2025")

    # Seed initial data if readings table is empty
    cursor.execute("SELECT COUNT(*) as count FROM readings")
    count = cursor.fetchone()['count']
    if count == 0:
        csv_path = os.path.join(os.path.dirname(settings.DB_PATH), "..", "data", "sample_readings.csv")
        csv_path = os.path.abspath(csv_path)
        if os.path.exists(csv_path):
            print(f"[DB] Seeding database from {csv_path}...")
            df = pd.read_csv(csv_path)
            records = []
            for _, row in df.iterrows():
                records.append((
                    row['timestamp'],
                    float(row['temperature']),
                    float(row['humidity']),
                    float(row['air_quality_ppm']),
                    int(row['motion_detected']),
                    int(row.get('motion_count', 0)),
                    int(row.get('fan_active', 0)),
                    int(row.get('risk_level', 0)),
                    0.95,
                    int(row.get('is_outlier', 0)),
                    'ESP32-NODE-01'
                ))
            cursor.executemany("""
                INSERT INTO readings (
                    timestamp, temperature, humidity, air_quality_ppm,
                    motion_detected, motion_count, fan_active,
                    risk_level, risk_confidence, is_outlier, device_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            print(f"[DB] Seeded {len(records)} readings.")
            
            # Seed initial sample alerts
            alerts_data = [
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'critical', 'High VOC / Air Stagnation Detected', 'MQ-135 reading reached 840 PPM with active occupancy. Automatic ventilation triggered.', 0),
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'warning', 'Thermal Comfort Index Rising', 'Room temperature exceeded 27.8°C with 64% RH.', 1),
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'info', 'Edge Node Connected', 'ESP32 secure mTLS session negotiated successfully.', 1)
            ]
            cursor.executemany("""
                INSERT INTO alerts (timestamp, severity, title, message, resolved)
                VALUES (?, ?, ?, ?, ?)
            """, alerts_data)

    conn.commit()
    conn.close()
