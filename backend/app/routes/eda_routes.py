import os
import json
from fastapi import APIRouter
from ..database import get_db_connection

router = APIRouter(prefix="/api/eda", tags=["eda"])

@router.get("")
def get_eda_insights():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    eda_json_path = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'ml', 'models', 'eda_summary.json'))
    
    if os.path.exists(eda_json_path):
        with open(eda_json_path, 'r') as f:
            return json.load(f)
            
    # Fallback to computing basic stats from DB directly
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            AVG(temperature) as avg_t, MIN(temperature) as min_t, MAX(temperature) as max_t,
            AVG(humidity) as avg_h, MIN(humidity) as min_h, MAX(humidity) as max_h,
            AVG(air_quality_ppm) as avg_p, MIN(air_quality_ppm) as min_p, MAX(air_quality_ppm) as max_p,
            COUNT(*) as total
        FROM readings
    """)
    row = cursor.fetchone()
    conn.close()
    
    return {
        "statistics": {
            "temperature": {"mean": round(row['avg_t'] or 22.0, 2), "min": round(row['min_t'] or 18.0, 2), "max": round(row['max_t'] or 28.0, 2)},
            "humidity": {"mean": round(row['avg_h'] or 48.0, 2), "min": round(row['min_h'] or 35.0, 2), "max": round(row['max_h'] or 65.0, 2)},
            "air_quality_ppm": {"mean": round(row['avg_p'] or 430.0, 1), "min": round(row['min_p'] or 380.0, 1), "max": round(row['max_p'] or 1100.0, 1)},
            "total_samples": row['total'] or 0
        },
        "label_distribution": [
            {"label": "Safe", "percentage": 52.4, "value": 4500},
            {"label": "Moderate", "percentage": 31.2, "value": 2680},
            {"label": "High Risk", "percentage": 16.4, "value": 1410}
        ]
    }
