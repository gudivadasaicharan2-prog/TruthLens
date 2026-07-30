from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
import os, uuid, json
import time
from app.ai.detectors.image_detector import analyze_image
from app.core.json_encoder import NumpyEncoder
from app.core.database import get_db
from app.core.security import get_user_email_header
from app.core.config import settings
from app.core.file_validation import validate_file_upload, validate_safe_file
from app.core.rate_limit import limiter, apply_rate_limit
from app.core.audit_logger import audit_logger
from app.core.logger import get_adapter
from app.core.metrics import PerformanceMetrics, measure_operation
from app.models.analysis import MediaAnalysis
from typing import Optional

router = APIRouter()

UPLOAD_DIR = "./uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = get_adapter("image")


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
@limiter.limit("10/minute")
async def analyze_image_endpoint(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_email: Optional[str] = Depends(get_user_email_header),
):
    # Initialize performance metrics
    metrics = PerformanceMetrics()
    metrics.start()
    
    logger.info("Image analysis request received", filename=file.filename, content_type=file.content_type)

    contents = await file.read()
    logger.info("File read", filename=file.filename, size_bytes=len(contents))

    # Validate file size
    if len(contents) > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        audit_logger.log_upload_failed(user_email, file.filename, f"File too large: {len(contents)} bytes")
        logger.warning("File size exceeded", filename=file.filename, size_bytes=len(contents), max_mb=max_mb)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_mb:.1f}MB"
        )

    # Save temporary file for validation
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    tmp_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")

    # Measure upload time
    with measure_operation("file_upload") as upload_ctx:
        with open(tmp_path, "wb") as f:
            f.write(contents)
    
    if upload_ctx.duration:
        metrics.record_upload(upload_ctx.duration)

    try:
        # Measure validation time
        with measure_operation("file_validation") as validation_ctx:
            is_valid, error_msg = validate_file_upload(
                filename=file.filename,
                content_type=file.content_type,
                file_size=len(contents),
                file_path=tmp_path,
                allowed_mime_types=settings.allowed_mime_types,
                max_file_size=settings.MAX_FILE_SIZE
            )

        if not is_valid:
            audit_logger.log_upload_failed(user_email, file.filename, error_msg)
            logger.warning("File validation failed", filename=file.filename, error=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)

        # Additional safety check
        if not validate_safe_file(tmp_path):
            audit_logger.log_upload_failed(user_email, file.filename, "File safety check failed")
            logger.warning("File safety check failed", filename=file.filename)
            raise HTTPException(
                status_code=400,
                detail="File validation failed. File may be corrupted or contain malicious content."
            )

        # Log upload completed
        audit_logger.log_upload_completed(user_email, file.filename, len(contents), metrics.metrics["upload_time"] or 0)
        logger.info("File upload completed", filename=file.filename, duration_seconds=metrics.metrics["upload_time"])

        # Log analysis started
        audit_logger.log_analysis_started(user_email, file.filename, "image")
        
        # Measure inference time
        with measure_operation("inference") as inference_ctx:
            result = await analyze_image(tmp_path)
        
        if inference_ctx.duration:
            metrics.record_inference(inference_ctx.duration)

        result["analysis_id"] = str(uuid.uuid4())
        result["filename"] = str(file.filename)

        # Save to user history
        _save_analysis(
            db, "image",
            result.get("verdict", "Unknown"),
            result.get("confidence", 0.0),
            user_email,
        )

        # Log analysis completed
        audit_logger.log_analysis_completed(
            user_email,
            file.filename,
            result.get("verdict", "Unknown"),
            result.get("confidence", 0.0),
            metrics.metrics["inference_time"] or 0
        )

        logger.info("Image analysis completed", 
                   filename=file.filename, 
                   verdict=result.get('verdict'),
                   confidence=result.get('confidence'),
                   duration_seconds=metrics.metrics["inference_time"])

        # Log report generation if applicable
        if result.get("report_path"):
            with measure_operation("pdf_generation") as pdf_ctx:
                # PDF generation already happened in analyze_image
                pass
            if pdf_ctx.duration:
                metrics.record_pdf_generation(pdf_ctx.duration)
            
            audit_logger.log_report_generated(
                user_email,
                file.filename,
                "PDF",
                metrics.metrics["pdf_generation_time"] or 0
            )
            logger.info("Report generated", filename=file.filename, report_path=result.get("report_path"))

        # Finish metrics collection
        final_metrics = metrics.finish()
        logger.info("Request completed", metrics_summary=final_metrics)

        # Add metrics to response (optional, for debugging)
        if settings.ENVIRONMENT != "production":
            result["performance_metrics"] = final_metrics

        json_str = json.dumps(result, cls=NumpyEncoder)

        return Response(content=json_str, media_type="application/json")

    except HTTPException:
        raise
    except Exception as e:
        audit_logger.log_analysis_failed(user_email, file.filename, str(e))
        logger.error("Image analysis failed", filename=file.filename, error=str(e))
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
