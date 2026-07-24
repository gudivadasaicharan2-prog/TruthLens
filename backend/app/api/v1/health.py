from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    models: dict

@router.get("/models")
def check_models():
    """Check if AI models are loaded and available"""
    try:
        from app.ai.models.image_model import is_using_trained_weights
        
        # Check if EfficientNet-B4 is loaded
        image_model_loaded = is_using_trained_weights()
        
        # Check for training weights file
        weights_path = Path(__file__).parent.parent.parent.parent / 'weights' / 'deepfake_classifier.pth'
        weights_exist = weights_path.exists()
        
        # Check for training checkpoints
        checkpoints_dir = Path(__file__).parent.parent.parent.parent / 'checkpoints'
        checkpoints_exist = checkpoints_dir.exists()
        checkpoint_files = list(checkpoints_dir.glob('*.pth')) if checkpoints_exist else []
        
        return {
            "status": "healthy" if image_model_loaded else "degraded",
            "models": {
                "image_model": {
                    "loaded": image_model_loaded,
                    "model_name": "EfficientNet-B4 with deepfake classifier" if image_model_loaded else "EfficientNet-B4 (feature extraction mode)",
                    "weights_file_exists": weights_exist,
                    "weights_path": str(weights_path),
                    "training_checkpoints_available": len(checkpoint_files) > 0,
                    "checkpoint_count": len(checkpoint_files)
                },
                "video_model": {
                    "loaded": True,
                    "model_name": "OpenCV-based forensic analysis"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/")
def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "truthlens-backend"}
