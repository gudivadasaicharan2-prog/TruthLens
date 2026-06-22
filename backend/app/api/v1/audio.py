from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import os, uuid, json
from app.services.audio_deepfake import analyze_audio
from app.core.json_encoder import NumpyEncoder
from app.core.database import get_db
from app.core.security import get_user_email_header
from app.models.analysis import MediaAnalysis
from typing import Optional

router = APIRouter()

UPLOAD_DIR = "./uploads/audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _email_to_uid(email: str):
    try:
        return uuid.UUID(str(uuid.uuid5(uuid.NAMESPACE_URL, email)))
    except Exception:
        return None


def _save_analysis(db, file_type: str, verdict: str, confidence: float, user_email):
    if db is None or not user_email:
        return
    try:
        uid = _email_to_uid(user_email)
        if uid is None:
            return
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
    return {"message": "Audio route working OK"}


@router.post("/analyze")
async def analyze_audio_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    print(f"[DEBUG] Audio analysis request received: {file.filename}")
    contents = await file.read()
    print(f"[DEBUG] Audio file size: {len(contents)} bytes")

    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB.")

    ext      = file.filename.split(".")[-1] if "." in file.filename else "mp3"
    tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")

    try:
        with open(tmp_path, "wb") as f:
            f.write(contents)

        print("[DEBUG] Calling analyze_audio service...")
        result = analyze_audio(tmp_path)
        print(f"[DEBUG] Audio verdict: {result.get('verdict', result.get('result', 'N/A'))}")

        result["analysis_id"] = str(uuid.uuid4())
        result["filename"]    = str(file.filename)

        # Save to user history
        verdict    = result.get("verdict") or result.get("result", "Unknown")
        confidence = result.get("confidence", 0.0)
        _save_analysis(db, "audio", verdict, confidence, user_email)

        json_str = json.dumps(result, cls=NumpyEncoder)
        print(f"[DEBUG] Returning JSON response (length: {len(json_str)})")
        return Response(content=json_str, media_type="application/json")

    except Exception as e:
        print(f"[ERROR] Audio analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
