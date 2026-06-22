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
        from app.services.image_deepfake import MODEL_1, MODEL_2
        from app.services.video_deepfake import MODEL
        from app.services.fake_news import NEWS_MODEL
        
        return {
            "status": "healthy" if all([MODEL_1, MODEL_2, MODEL, NEWS_MODEL]) else "degraded",
            "models": {
                "image_model_1": {
                    "loaded": MODEL_1 is not None,
                    "model_name": "dima806/deepfake_detection" if MODEL_1 else "Not loaded"
                },
                "image_model_2": {
                    "loaded": MODEL_2 is not None,
                    "model_name": "Ahmed1295/deepfake-detection" if MODEL_2 else "Not loaded"
                },
                "video_model": {
                    "loaded": MODEL is not None,
                    "model_name": "dima806/deepfake_detection" if MODEL else "Not loaded"
                },
                "news_model": {
                    "loaded": NEWS_MODEL is not None,
                    "model_name": "mrm8488/bert-tiny-finetuned-fake-news" if NEWS_MODEL else "Not loaded"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/")
def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "truthlens-backend"}
