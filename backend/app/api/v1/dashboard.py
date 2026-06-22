from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_user_email_header
from app.models.analysis import MediaAnalysis
from app.models.user import User
from datetime import datetime, timedelta
from typing import Optional
import uuid

router = APIRouter()


def _email_to_uid(email: str) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(uuid.uuid5(uuid.NAMESPACE_URL, email)))
    except Exception:
        return None


@router.get("/{uid}/statistics")
async def get_stats(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    try:
        if not user_email or str(_email_to_uid(user_email)) != uid:
            raise HTTPException(status_code=403, detail="Not authorized")
        user_uuid = uuid.UUID(uid)

        def q_count(extra_filter=None):
            q = db.query(func.count(MediaAnalysis.media_id))
            q = q.filter(MediaAnalysis.user_id == user_uuid)
            if extra_filter is not None:
                q = q.filter(extra_filter)
            return q.scalar() or 0

        total_users = db.query(func.count(User.user_id)).scalar() or 0

        return {
            "total_users":        total_users,
            "total_analyses":     q_count(),
            "image_analyses":     q_count(MediaAnalysis.file_type == "image"),
            "video_analyses":     q_count(MediaAnalysis.file_type == "video"),
            "audio_analyses":     q_count(MediaAnalysis.file_type == "audio"),
            "ai_generated_count": q_count(MediaAnalysis.result.ilike("%ai generated%")),
            "deepfakes_detected": q_count(MediaAnalysis.result.ilike("%deepfake%")),
            "authentic_count":    q_count(MediaAnalysis.result.ilike("%authentic%")),
            "suspicious_count":   q_count(MediaAnalysis.result.ilike("%suspicious%")),
            "manipulated_count":  q_count(MediaAnalysis.result.ilike("%manipulated%")),
            "last_updated":       datetime.now().strftime("%d %b %Y, %I:%M %p"),
        }
    except Exception as e:
        return {
            "total_users": 0, "total_analyses": 0,
            "image_analyses": 0, "video_analyses": 0, "audio_analyses": 0,
            "ai_generated_count": 0, "deepfakes_detected": 0,
            "authentic_count": 0, "suspicious_count": 0,
            "manipulated_count": 0, "error": str(e),
        }


@router.get("/{uid}/daily")
async def get_daily(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    try:
        if not user_email or str(_email_to_uid(user_email)) != uid:
            raise HTTPException(status_code=403, detail="Not authorized")
        user_uuid = uuid.UUID(uid)
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
            aud = day_count("audio")
            days.append({"date": date_str, "image": img, "video": vid, "audio": aud, "total": img + vid + aud})

        return {"daily": days}
    except Exception as e:
        return {"daily": [], "error": str(e)}


@router.get("/{uid}/recent")
async def get_recent(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    try:
        if not user_email or str(_email_to_uid(user_email)) != uid:
            raise HTTPException(status_code=403, detail="Not authorized")
        user_uuid = uuid.UUID(uid)
        q   = db.query(MediaAnalysis).order_by(MediaAnalysis.created_at.desc())
        q = q.filter(MediaAnalysis.user_id == user_uuid)
        media_rows = q.limit(10).all()

        type_icons = {"image": "Image", "video": "Video", "audio": "Audio"}
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
    except Exception as e:
        return {"recent": [], "error": str(e)}


@router.get("/{uid}/topics")
async def get_topics(
    uid: str,
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    """Return recent high-confidence detections for the current user."""
    try:
        if not user_email or str(_email_to_uid(user_email)) != uid:
            raise HTTPException(status_code=403, detail="Not authorized")
        user_uuid = uuid.UUID(uid)
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
    except Exception as e:
        return {"topics": [], "error": str(e)}
