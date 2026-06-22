from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import os, uuid, json
from app.services.video_deepfake import analyze_video
from app.core.json_encoder import NumpyEncoder
from app.core.database import get_db
from app.core.security import get_user_email_header
from app.models.analysis import MediaAnalysis
from typing import Optional

router = APIRouter()

UPLOAD_DIR = "./uploads/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v", "3gp", "flv"}
ALLOWED_MIME_TYPES  = {
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "video/x-matroska", "video/webm", "video/x-m4v",
    "video/3gpp", "video/x-flv",
    "application/octet-stream",
}
MAX_SIZE_BYTES = 150 * 1024 * 1024


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

ALLOWED_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v", "3gp", "flv"}
ALLOWED_MIME_TYPES  = {
    "video/mp4", "video/quicktime", "video/x-msvideo",
    "video/x-matroska", "video/webm", "video/x-m4v",
    "video/3gpp", "video/x-flv",
    # Some browsers send generic types
    "application/octet-stream",
}
MAX_SIZE_BYTES = 150 * 1024 * 1024   # 150 MB


@router.get("/test")
async def test():
    return {"message": "Video route working OK"}


@router.post("/analyze")
async def analyze_video_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    print(f"[VIDEO API] Request: filename={file.filename!r}, "
          f"content_type={file.content_type!r}")

    # ── Extension check (primary gate — MIME types are unreliable) ──
    raw_ext = (file.filename or "").rsplit(".", 1)
    ext     = raw_ext[-1].lower() if len(raw_ext) == 2 else ""

    if ext not in ALLOWED_EXTENSIONS:
        print(f"[VIDEO API] Rejected extension: .{ext}")
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported video format: .{ext or '(none)'}. "
                f"Accepted formats: {', '.join(sorted(ALLOWED_EXTENSIONS)).upper()}."
            ),
        )

    # ── Read & size check ───────────────────────────────────────────
    contents = await file.read()
    size_mb  = len(contents) / (1024 * 1024)
    print(f"[VIDEO API] File size: {size_mb:.2f} MB")

    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed size is 150 MB.",
        )

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # ── Write to temp file ──────────────────────────────────────────
    tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")
    try:
        with open(tmp_path, "wb") as f:
            f.write(contents)
        print(f"[VIDEO API] Saved to temp: {tmp_path}")

        # ── Analyze ─────────────────────────────────────────────────
        print("[VIDEO API] Calling analyze_video service ...")
        result = await analyze_video(tmp_path)

        verdict    = result.get("verdict", "Unknown")
        confidence = result.get("confidence", 0.0)
        print(f"[VIDEO API] Result -> verdict={verdict!r}, "
              f"confidence={confidence:.2f}, "
              f"ai_prob={result.get('ai_probability', '?')}%, "
              f"deepfake_prob={result.get('deepfake_probability', '?')}%")

        result["analysis_id"] = str(uuid.uuid4())
        result["filename"]    = str(file.filename)

        # Save to user history
        _save_analysis(db, "video",
            result.get("verdict", "Unknown"),
            result.get("confidence", 0.0),
            user_email,
        )

        json_str = json.dumps(result, cls=NumpyEncoder)
        print(f"[VIDEO API] Returning JSON ({len(json_str)} bytes)")
        return Response(content=json_str, media_type="application/json")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[VIDEO API] ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Video analysis failed: {str(e)}",
        )
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                print(f"[VIDEO API] Cleaned up temp file")
            except Exception:
                pass
