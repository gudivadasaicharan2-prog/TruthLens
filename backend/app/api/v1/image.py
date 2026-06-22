from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import os, uuid, json
from app.services.image_deepfake import analyze_image
from app.core.json_encoder import NumpyEncoder
from app.core.database import get_db
from app.core.security import get_user_email_header
from app.models.analysis import MediaAnalysis
from typing import Optional

router = APIRouter()

UPLOAD_DIR = "./uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg", "image/jpg", "image/png",
    "image/webp", "image/gif", "image/bmp",
}


def _email_to_uid(email: str) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(uuid.uuid5(uuid.NAMESPACE_URL, email)))
    except Exception:
        return None


def _save_analysis(db, file_type: str, verdict: str, confidence: float, user_email: Optional[str]):
    """Save analysis result to history. Silently skips if DB unavailable."""
    if db is None:
        return
    try:
        uid = _email_to_uid(user_email) if user_email else None
        if uid is None:
            return  # Don't save anonymous analyses
        record = MediaAnalysis(
            media_id=uuid.uuid4(),
            user_id=uid,
            file_type=file_type,
            result=verdict,
            confidence=float(confidence) if confidence else 0.0,
        )
        db.add(record)
        db.commit()
        print(f"[HISTORY] Saved {file_type} analysis for {user_email}")
    except Exception as e:
        print(f"[HISTORY] Save error: {e}")
        try:
            db.rollback()
        except Exception:
            pass


@router.get("/test")
async def test():
    return {"message": "Image route working OK"}


@router.post("/analyze")
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    print(f"[DEBUG] Image analysis request: {file.filename} ({file.content_type})")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: JPG, PNG, WEBP, GIF.",
        )

    contents = await file.read()
    print(f"[DEBUG] File size: {len(contents)} bytes")

    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10 MB.")

    ext      = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")

    try:
        with open(tmp_path, "wb") as f:
            f.write(contents)

        result = await analyze_image(tmp_path)

        result["analysis_id"] = str(uuid.uuid4())
        result["filename"]    = str(file.filename)

        # Save to user history
        _save_analysis(
            db, "image",
            result.get("verdict", "Unknown"),
            result.get("confidence", 0.0),
            user_email,
        )

        json_str = json.dumps(result, cls=NumpyEncoder)
        print(f"[DEBUG] Image result: verdict={result.get('verdict')}, "
              f"confidence={result.get('confidence')}, ai_prob={result.get('ai_probability')}%")

        return Response(content=json_str, media_type="application/json")

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Image analysis failed: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
