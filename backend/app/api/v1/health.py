from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
        
        return {
            "status": "healthy" if image_model_loaded else "degraded",
            "models": {
                "image_model": {
                    "loaded": image_model_loaded,
                    "model_name": "EfficientNet-B4 with deepfake classifier" if image_model_loaded else "EfficientNet-B4 (feature extraction mode)"
                },
                "video_model": {
                    "loaded": True,
                    "model_name": "OpenCV-based forensic analysis"
                },
                "audio_model": {
                    "loaded": True,
                    "model_name": "Librosa-based heuristic analysis"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/")
def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "truthlens-backend"}
