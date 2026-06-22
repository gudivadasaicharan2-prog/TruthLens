from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_user_email_header
from app.models.analysis import MediaAnalysis
from typing import Optional
import uuid

router = APIRouter(tags=["users"])


def _email_to_user_id(email: str) -> str:
    """Deterministic user_id from email — same algorithm used in auth.py."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, email))


@router.get("/{uid}/history")
def get_user_history(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    """Return media analysis history scoped to the authenticated user."""
    if not user_email or _email_to_user_id(user_email) != uid:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's data")

    if db is None:
        return []

    type_icons = {"image": "Image", "video": "Video", "audio": "Audio"}
    try:
        q = db.query(MediaAnalysis).order_by(MediaAnalysis.created_at.desc())

        # Filter by user if authenticated
        if user_email:
            uid_str = _email_to_user_id(user_email)
            try:
                uid = uuid.UUID(uid_str)
                q = q.filter(MediaAnalysis.user_id == uid)
            except Exception:
                pass

        media_analyses = q.limit(100).all()

        history = []
        for a in media_analyses:
            ft = (a.file_type or "media").lower()
            history.append({
                "analysis_id": str(a.media_id),
                "type":        ft.capitalize(),
                "icon":        type_icons.get(ft, "File"),
                "result":      a.result or "Unknown",
                "confidence":  a.confidence,
                "created_at":  a.created_at.isoformat() if a.created_at else None,
                "title":       f"{ft.capitalize()} file analysis",
            })
        return history

    except Exception as e:
        print(f"[HISTORY] Error: {e}")
        return []


@router.delete("/{uid}/history/{analysis_id}")
def delete_history_item(
    uid: str,
    analysis_id: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    """Delete a single media analysis history entry (must belong to current user)."""
    if not user_email or _email_to_user_id(user_email) != uid:
        raise HTTPException(status_code=403, detail="Not authorized to modify this user's data")

    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    try:
        uid = uuid.UUID(analysis_id)
        q   = db.query(MediaAnalysis).filter(MediaAnalysis.media_id == uid)

        # Scope deletion to user
        if user_email:
            owner_id = uuid.UUID(_email_to_user_id(user_email))
            q = q.filter(MediaAnalysis.user_id == owner_id)

        row = q.first()
        if not row:
            raise HTTPException(status_code=404, detail="Analysis not found")
        db.delete(row)
        db.commit()
        return {"success": True, "deleted_id": analysis_id}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DELETE HISTORY] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{uid}/profile")
def get_user_profile(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    """Return user-specific statistics for the Profile page."""
    if not user_email or _email_to_user_id(user_email) != uid:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's profile")

    uid_str = uid
    stats = {
        "user_id":          uid_str,
        "email":            user_email,
        "total_analyses":   0,
        "image_analyses":   0,
        "video_analyses":   0,
        "audio_analyses":   0,
        "authentic_count":  0,
        "flagged_count":    0,
    }

    if db is None:
        return stats

    try:
        uid = uuid.UUID(uid_str)
        base_q = db.query(func.count(MediaAnalysis.media_id)).filter(
            MediaAnalysis.user_id == uid
        )
        stats["total_analyses"] = base_q.scalar() or 0
        stats["image_analyses"] = base_q.filter(MediaAnalysis.file_type == "image").scalar() or 0
        stats["video_analyses"] = base_q.filter(MediaAnalysis.file_type == "video").scalar() or 0
        stats["audio_analyses"] = base_q.filter(MediaAnalysis.file_type == "audio").scalar() or 0
        stats["authentic_count"] = db.query(func.count(MediaAnalysis.media_id)).filter(
            MediaAnalysis.user_id == uid,
            MediaAnalysis.result.ilike("%authentic%"),
        ).scalar() or 0
        stats["flagged_count"] = db.query(func.count(MediaAnalysis.media_id)).filter(
            MediaAnalysis.user_id == uid,
            MediaAnalysis.result.ilike("%deepfake%") |
            MediaAnalysis.result.ilike("%ai generated%") |
            MediaAnalysis.result.ilike("%suspicious%") |
            MediaAnalysis.result.ilike("%manipulated%"),
        ).scalar() or 0
    except Exception as e:
        print(f"[PROFILE] Stats error: {e}")

    return stats
