from fastapi import APIRouter
from ..schemas import DeviceStatusResponse, ActuationRequest
from ..mqtt_service import mqtt_service

router = APIRouter(prefix="/api/device", tags=["device"])

@router.get("/status", response_model=DeviceStatusResponse)
def get_device_status():
    return DeviceStatusResponse(**mqtt_service.latest_status)

@router.post("/actuate")
def actuate_device(req: ActuationRequest):
    if req.action in ["FAN_ON", "FAN_OFF"]:
        mqtt_service.auto_fan = False
        mqtt_service.actuate_fan(req.action, req.reason or "User dashboard manual toggle")
    elif req.action == "AUTO":
        mqtt_service.auto_fan = True
        
    return {
        "status": "success",
        "action": req.action,
        "fan_state": mqtt_service.fan_state,
        "auto_mode": mqtt_service.auto_fan,
        "message": f"Ventilation actuation set to {req.action}"
    }
