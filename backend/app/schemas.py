from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ReadingCreate(BaseModel):
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., description="Relative humidity percentage")
    air_quality_ppm: float = Field(..., description="MQ-135 reading in PPM")
    motion_detected: int = Field(0, description="1 if motion triggered, 0 otherwise")
    motion_count: Optional[int] = Field(0, description="PIR pulse count in 30s window")
    fan_active: Optional[int] = Field(0, description="1 if fan active, 0 otherwise")
    timestamp: Optional[str] = None
    device_id: Optional[str] = "ESP32-NODE-01"

class ReadingResponse(ReadingCreate):
    id: int
    risk_level: int
    risk_confidence: float
    is_outlier: int

class PredictRequest(BaseModel):
    temperature: float = Field(22.5, description="Temperature in Celsius")
    humidity: float = Field(48.0, description="Relative humidity in %")
    air_quality_ppm: float = Field(420.0, description="Air quality in PPM")
    motion_detected: int = Field(1, description="Binary occupancy")
    consecutive_occupied_minutes: Optional[float] = Field(15.0, description="Occupancy duration")

class PredictResponse(BaseModel):
    risk_level: int
    risk_label: str # "Safe", "Moderate", "High Risk"
    confidence: float
    probabilities: Dict[str, float]
    top_contributing_factors: List[Dict[str, Any]]
    recommendations: List[str]

class AlertResponse(BaseModel):
    id: int
    timestamp: str
    severity: str
    title: str
    message: str
    resolved: int

class DeviceStatusResponse(BaseModel):
    device_id: str
    online: bool
    ip_address: str
    wifi_rssi_dbm: int
    firmware_version: str
    uptime_seconds: int
    free_heap_bytes: int
    sampling_interval_sec: int
    tls_secured: bool
    tls_cipher: str
    sensors: Dict[str, Any]
    last_seen: str

class ActuationRequest(BaseModel):
    action: str # "FAN_ON", "FAN_OFF", "AUTO"
    reason: Optional[str] = "Manual dashboard trigger"

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
