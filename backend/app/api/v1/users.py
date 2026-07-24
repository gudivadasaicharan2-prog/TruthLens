from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_user_email_header
from app.models.analysis import MediaAnalysis
from app.models.user import User
from typing import Optional
from datetime import datetime, timedelta
import uuid

router = APIRouter(tags=["users"])


def _email_to_user_id(email: str) -> str:
    """Deterministic user_id from email — same algorithm used in auth.py."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, email))


def _get_authenticated_user_uuid(user_email: Optional[str]) -> uuid.UUID:
    """Helper: derive user UUID from authenticated email.
    
    The URL uid parameter is only for route compatibility with frontend.
    Actual authorization is based solely on the X-User-Email header.
    """
    if not user_email:
        raise HTTPException(status_code=403, detail="Not authorized")
    return uuid.UUID(_email_to_user_id(user_email))


# ── Dashboard Statistics ─────────────────────────────────────────────────────
@router.get("/{uid}/statistics")
async def get_stats(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    user_uuid = _get_authenticated_user_uuid(user_email)

    def q_count(extra_filter=None):
        q = db.query(func.count(MediaAnalysis.media_id))
        q = q.filter(MediaAnalysis.user_id == user_uuid)
        if extra_filter is not None:
            q = q.filter(extra_filter)
        return q.scalar() or 0

    total_users = db.query(func.count(User.user_id)).scalar() or 0

    return {
        "total_users":        total_users,
        "total_analyses":     q_count(MediaAnalysis.file_type.in_(["image", "video"])),
        "image_analyses":     q_count(MediaAnalysis.file_type == "image"),
        "video_analyses":     q_count(MediaAnalysis.file_type == "video"),
        "ai_generated_count": q_count(MediaAnalysis.result.ilike("%ai generated%")),
        "deepfakes_detected": q_count(MediaAnalysis.result.ilike("%deepfake%")),
        "authentic_count":    q_count(MediaAnalysis.result.ilike("%authentic%")),
        "suspicious_count":   q_count(MediaAnalysis.result.ilike("%suspicious%")),
        "manipulated_count":  q_count(MediaAnalysis.result.ilike("%manipulated%")),
        "last_updated":       datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }


@router.get("/{uid}/daily")
async def get_daily(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    user_uuid = _get_authenticated_user_uuid(user_email)
    today = datetime.now()
    days  = []

    for i in range(29, -1, -1):
        day = today - timedelta(days=i)
        date_str = day.strftime("%d %b")

        def day_count(ft):
            q = db.query(func.count(MediaAnalysis.media_id)).filter(
                MediaAnalysis.file_type == ft,
                func.date(MediaAnalysis.created_at) == day.date()
            )
            q = q.filter(MediaAnalysis.user_id == user_uuid)
            return q.scalar() or 0

        img = day_count("image")
        vid = day_count("video")
        days.append({"date": date_str, "image": img, "video": vid, "total": img + vid})

    return {"daily": days}


@router.get("/{uid}/recent")
async def get_recent(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    user_uuid = _get_authenticated_user_uuid(user_email)
    q   = db.query(MediaAnalysis).order_by(MediaAnalysis.created_at.desc())
    q = q.filter(MediaAnalysis.user_id == user_uuid)
    media_rows = q.limit(10).all()

    type_icons = {"image": "Image", "video": "Video"}
    recent = []
    for row in media_rows:
        ft = row.file_type or "media"
        recent.append({
            "id":         str(row.media_id),
            "type":       ft.capitalize(),
            "icon":       type_icons.get(ft, "File"),
            "summary":    f"{ft.capitalize()} analysis",
            "result":     row.result or "Unknown",
            "confidence": f"{round(row.confidence * 100)}%" if row.confidence else "N/A",
            "date":       row.created_at.strftime("%d %b %Y, %I:%M %p") if row.created_at else "—",
        })
    return {"recent": recent}


@router.get("/{uid}/topics")
async def get_topics(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    """Return recent high-confidence detections for the current user."""
    user_uuid = _get_authenticated_user_uuid(user_email)
    q   = db.query(MediaAnalysis).filter(
        MediaAnalysis.result.ilike("%deepfake%") |
        MediaAnalysis.result.ilike("%ai generated%") |
        MediaAnalysis.result.ilike("%manipulated%")
    ).order_by(MediaAnalysis.created_at.desc())
    q = q.filter(MediaAnalysis.user_id == user_uuid)
    flagged = q.limit(5).all()

    topics = [
        {
            "title":      f"{(row.file_type or 'media').capitalize()} - {row.result}",
            "confidence": round(row.confidence * 100) if row.confidence else 0,
            "date":       row.created_at.strftime("%d %b %Y") if row.created_at else "—",
        }
        for row in flagged
    ]
    return {"topics": topics}


# ── User History ─────────────────────────────────────────────────────────────
@router.get("/{uid}/history")
def get_user_history(
    uid: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    """Return media analysis history scoped to the authenticated user."""
    user_uuid = _get_authenticated_user_uuid(user_email)

    if db is None:
        return []

    type_icons = {"image": "Image", "video": "Video"}
    q = db.query(MediaAnalysis).order_by(MediaAnalysis.created_at.desc())
    q = q.filter(MediaAnalysis.user_id == user_uuid)
    q = q.filter(MediaAnalysis.file_type.in_(["image", "video"]))

    total = q.count()
    media_analyses = q.offset(skip).limit(limit).all()

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
    return {
        "items": history,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.delete("/{uid}/history/{analysis_id}")
def delete_history_item(
    uid: str,
    analysis_id: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    """Delete a single media analysis history entry (must belong to current user)."""
    user_uuid = _get_authenticated_user_uuid(user_email)

    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    analysis_uuid = uuid.UUID(analysis_id)
    q = db.query(MediaAnalysis).filter(MediaAnalysis.media_id == analysis_uuid)
    q = q.filter(MediaAnalysis.user_id == user_uuid)

    row = q.first()
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    db.delete(row)
    db.commit()
    return {"success": True, "deleted_id": analysis_id}


@router.get("/{uid}/profile")
def get_user_profile(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    """Return user-specific statistics for the Profile page."""
    user_uuid = _get_authenticated_user_uuid(user_email)

    stats = {
        "user_id":          str(user_uuid),
        "email":            user_email,
        "total_analyses":   0,
        "image_analyses":   0,
        "video_analyses":   0,
        "authentic_count":  0,
        "flagged_count":    0,
    }

    if db is None:
        return stats

    base_q = db.query(func.count(MediaAnalysis.media_id)).filter(
        MediaAnalysis.user_id == user_uuid,
        MediaAnalysis.file_type.in_(["image", "video"])
    )
    stats["total_analyses"] = base_q.scalar() or 0
    stats["image_analyses"] = base_q.filter(MediaAnalysis.file_type == "image").scalar() or 0
    stats["video_analyses"] = base_q.filter(MediaAnalysis.file_type == "video").scalar() or 0
    stats["authentic_count"] = db.query(func.count(MediaAnalysis.media_id)).filter(
        MediaAnalysis.user_id == user_uuid,
        MediaAnalysis.result.ilike("%authentic%"),
    ).scalar() or 0
    stats["flagged_count"] = db.query(func.count(MediaAnalysis.media_id)).filter(
        MediaAnalysis.user_id == user_uuid,
        MediaAnalysis.result.ilike("%deepfake%") |
        MediaAnalysis.result.ilike("%ai generated%") |
        MediaAnalysis.result.ilike("%suspicious%") |
        MediaAnalysis.result.ilike("%manipulated%"),
    ).scalar() or 0

    return stats
