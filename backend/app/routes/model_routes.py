import subprocess
import os
import sys
from fastapi import APIRouter, Depends
from ..schemas import PredictRequest, PredictResponse
from ..ml_service import ml_service
from ..auth import get_current_user

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("/metrics")
def get_metrics():
    return ml_service.get_metrics()

@router.post("/retrain")
def retrain_model(current_user: dict = Depends(get_current_user)):
    """Triggers model re-training pipeline on updated data."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        train_script = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'ml', 'train.py'))
        
        result = subprocess.run([sys.executable, train_script], capture_output=True, text=True, check=True)
        # Reload models in memory
        ml_service.load_models()
        
        return {
            "status": "success",
            "message": "Model retrained successfully",
            "metrics": ml_service.get_metrics(),
            "output_log": result.stdout[-500:] if result.stdout else ""
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Training failed: {e}"
        }

@router.post("/predict", response_model=PredictResponse)
def predict_risk_endpoint(req: PredictRequest):
    res = ml_service.predict_risk(
        temp=req.temperature,
        humidity=req.humidity,
        ppm=req.air_quality_ppm,
        motion=req.motion_detected,
        occupancy_persistence=req.consecutive_occupied_minutes / 0.5 # 30s steps
    )
    return PredictResponse(**res)
