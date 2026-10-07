import io
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, UploadFile, File, HTTPException, Depends
from ..database import get_db_connection
from ..schemas import ReadingCreate, ReadingResponse
from ..ml_service import ml_service
from ..mqtt_service import mqtt_service
from ..auth import get_current_user

router = APIRouter(prefix="/api/readings", tags=["readings"])

@router.get("")
def get_readings(
    time_range: str = Query("24h", description="1h, 6h, 24h, 7d, all"),
    limit: int = Query(100, ge=1, le=5000),
    offset: int = Query(0, ge=0),
    filter_outliers: bool = Query(False, description="Exclude anomalous spikes"),
    search: Optional[str] = Query(None, description="Search term in timestamp or device")
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Time filtering
    now = datetime.now()
    time_filter = ""
    params = []
    
    if time_range == "1h":
        cutoff = (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        time_filter = "WHERE timestamp >= ?"
        params.append(cutoff)
    elif time_range == "6h":
        cutoff = (now - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
        time_filter = "WHERE timestamp >= ?"
        params.append(cutoff)
    elif time_range == "24h":
        cutoff = (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        time_filter = "WHERE timestamp >= ?"
        params.append(cutoff)
    elif time_range == "7d":
        cutoff = (now - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        time_filter = "WHERE timestamp >= ?"
        params.append(cutoff)
    else:
        time_filter = "WHERE 1=1"

    if filter_outliers:
        time_filter += " AND is_outlier = 0"
        
    if search:
        time_filter += " AND (timestamp LIKE ? OR device_id LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    # Count total
    count_query = f"SELECT COUNT(*) as total FROM readings {time_filter}"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()['total']

    # Get records
    select_query = f"""
        SELECT id, timestamp, temperature, humidity, air_quality_ppm,
               motion_detected, motion_count, fan_active, risk_level,
               risk_confidence, is_outlier, device_id
        FROM readings
        {time_filter}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(select_query, params)
    rows = cursor.fetchall()
    
    # Summary stats
    stats_query = f"""
        SELECT 
            AVG(temperature) as avg_temp,
            AVG(humidity) as avg_hum,
            AVG(air_quality_ppm) as avg_ppm,
            SUM(is_outlier) as outlier_count,
            COUNT(*) as total_samples
        FROM readings {time_filter}
    """
    cursor.execute(stats_query, params[:-2])
    stats_row = cursor.fetchone()
    conn.close()

    items = [dict(row) for row in rows]
    return {
        "items": items,
        "total": total_count,
        "limit": limit,
        "offset": offset,
        "summary": {
            "avg_temp": round(stats_row['avg_temp'] or 0, 2),
            "avg_hum": round(stats_row['avg_hum'] or 0, 2),
            "avg_ppm": round(stats_row['avg_ppm'] or 0, 1),
            "outlier_count": int(stats_row['outlier_count'] or 0),
            "total_samples": int(stats_row['total_samples'] or 0)
        }
    }

@router.get("/latest")
def get_latest_reading():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, temperature, humidity, air_quality_ppm,
               motion_detected, motion_count, fan_active, risk_level,
               risk_confidence, is_outlier, device_id
        FROM readings
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        # Fallback default
        return {
            "id": 1,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "temperature": 22.4,
            "humidity": 45.8,
            "air_quality_ppm": 412.0,
            "motion_detected": 1,
            "motion_count": 4,
            "fan_active": 0,
            "risk_level": 0,
            "risk_confidence": 0.96,
            "is_outlier": 0,
            "device_id": "ESP32-NODE-01"
        }
    return dict(row)

@router.post("")
def ingest_reading(reading: ReadingCreate):
    ts = reading.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # ML inference
    pred = ml_service.predict_risk(
        reading.temperature, reading.humidity, reading.air_quality_ppm, reading.motion_detected
    )
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO readings (
            timestamp, temperature, humidity, air_quality_ppm,
            motion_detected, motion_count, fan_active,
            risk_level, risk_confidence, is_outlier, device_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts, reading.temperature, reading.humidity, reading.air_quality_ppm,
        reading.motion_detected, reading.motion_count or 0, reading.fan_active or 0,
        pred['risk_level'], pred['confidence'], 0, reading.device_id or 'ESP32-NODE-01'
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "id": new_id,
        "prediction": pred
    }

@router.post("/upload-csv")
async def upload_readings_csv(
    file: UploadFile = File(...),
    replace_existing: bool = Query(False, description="Replace DB or append"),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    content = await file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {e}")
        
    required_cols = {'temperature', 'humidity', 'air_quality_ppm'}
    if not required_cols.issubset(set(df.columns)):
        raise HTTPException(status_code=400, detail=f"CSV must contain: {required_cols}")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if replace_existing:
        cursor.execute("DELETE FROM readings;")
        
    records = []
    for _, row in df.iterrows():
        ts = row.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        temp = float(row['temperature'])
        hum = float(row['humidity'])
        ppm = float(row['air_quality_ppm'])
        motion = int(row.get('motion_detected', 0))
        motion_count = int(row.get('motion_count', 0))
        fan = int(row.get('fan_active', 0))
        risk = int(row.get('risk_level', 0))
        outlier = int(row.get('is_outlier', 0))
        
        records.append((
            str(ts), temp, hum, ppm, motion, motion_count, fan, risk, 0.95, outlier, 'ESP32-IMPORTED'
        ))
        
    cursor.executemany("""
        INSERT INTO readings (
            timestamp, temperature, humidity, air_quality_ppm,
            motion_detected, motion_count, fan_active,
            risk_level, risk_confidence, is_outlier, device_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "rows_imported": len(records),
        "action": "replaced" if replace_existing else "appended"
    }
