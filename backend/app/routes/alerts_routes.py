from typing import List
from fastapi import APIRouter
from ..database import get_db_connection
from ..schemas import AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("", response_model=List[AlertResponse])
def get_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, severity, title, message, resolved
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT 50
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "alert_id": alert_id, "resolved": 1}
