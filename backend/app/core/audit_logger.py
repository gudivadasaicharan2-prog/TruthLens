"""
Audit Logging Module
====================
Implements structured security event logging for compliance and monitoring.
Logs security events without exposing secrets or sensitive data.
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request
from app.core.config import settings


class AuditLogger:
    """
    Structured audit logger for security events.
    
    Logs the following events:
    - Upload started
    - Upload completed
    - Analysis completed
    - Report generated
    - Authentication events
    - Errors and failures
    
    Never logs:
    - Secrets or passwords
    - Uploaded image contents
    - Sensitive user data
    """
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # JSON formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)
    
    def _log_event(
        self,
        event_type: str,
        user_id: Optional[str],
        details: Dict[str, Any],
        status: str = "success",
        error: Optional[str] = None
    ) -> None:
        """
        Log an audit event with structured data.
        
        Args:
            event_type: Type of event (upload, analysis, auth, etc.)
            user_id: User identifier (email or user ID)
            details: Event details dictionary
            status: Event status (success, failure, error)
            error: Error message if applicable
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": self._sanitize_user_id(user_id),
            "status": status,
            "environment": settings.ENVIRONMENT,
            "details": self._sanitize_details(details)
        }
        
        if error:
            log_entry["error"] = error
        
        log_message = json.dumps(log_entry)
        
        if status == "success":
            self.logger.info(log_message)
        elif status == "failure":
            self.logger.warning(log_message)
        else:
            self.logger.error(log_message)
    
    def _sanitize_user_id(self, user_id: Optional[str]) -> Optional[str]:
        """
        Sanitize user ID for logging.
        
        Args:
            user_id: User identifier
            
        Returns:
            Sanitized user ID (hashed or truncated)
        """
        if not user_id:
            return None
        
        # Hash email addresses for privacy
        if "@" in user_id:
            import hashlib
            return hashlib.sha256(user_id.encode()).hexdigest()[:16]
        
        return user_id[:16]  # Truncate long IDs
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize details dictionary to remove sensitive information.
        
        Args:
            details: Original details dictionary
            
        Returns:
            Sanitized details dictionary
        """
        sanitized = {}
        
        sensitive_keys = [
            'password', 'secret', 'token', 'api_key', 'private_key',
            'authorization', 'cookie', 'session', 'credit_card',
            'ssn', 'social_security', 'image_data', 'file_content'
        ]
        
        for key, value in details.items():
            # Skip sensitive keys
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 200:
                # Truncate long strings
                sanitized[key] = value[:200] + "..."
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_upload_started(
        self,
        user_id: Optional[str],
        filename: str,
        file_size: int,
        content_type: str
    ) -> None:
        """
        Log file upload started event.
        
        Args:
            user_id: User identifier
            filename: Name of the file being uploaded
            file_size: Size of the file in bytes
            content_type: MIME type of the file
        """
        details = {
            "filename": filename,
            "file_size": file_size,
            "content_type": content_type
        }
        
        self._log_event(
            event_type="upload_started",
            user_id=user_id,
            details=details,
            status="success"
        )
    
    def log_upload_completed(
        self,
        user_id: Optional[str],
        filename: str,
        file_size: int,
        duration_seconds: float
    ) -> None:
        """
        Log file upload completed event.
        
        Args:
            user_id: User identifier
            filename: Name of the uploaded file
            file_size: Size of the file in bytes
            duration_seconds: Time taken to upload
        """
        details = {
            "filename": filename,
            "file_size": file_size,
            "duration_seconds": duration_seconds
        }
        
        self._log_event(
            event_type="upload_completed",
            user_id=user_id,
            details=details,
            status="success"
        )
    
    def log_upload_failed(
        self,
        user_id: Optional[str],
        filename: str,
        error: str
    ) -> None:
        """
        Log file upload failed event.
        
        Args:
            user_id: User identifier
            filename: Name of the file
            error: Error message
        """
        details = {
            "filename": filename
        }
        
        self._log_event(
            event_type="upload_failed",
            user_id=user_id,
            details=details,
            status="failure",
            error=error
        )
    
    def log_analysis_started(
        self,
        user_id: Optional[str],
        filename: str,
        analysis_type: str = "image"
    ) -> None:
        """
        Log analysis started event.
        
        Args:
            user_id: User identifier
            filename: Name of the file being analyzed
            analysis_type: Type of analysis (image, video, etc.)
        """
        details = {
            "filename": filename,
            "analysis_type": analysis_type
        }
        
        self._log_event(
            event_type="analysis_started",
            user_id=user_id,
            details=details,
            status="success"
        )
    
    def log_analysis_completed(
        self,
        user_id: Optional[str],
        filename: str,
        verdict: str,
        confidence: float,
        duration_seconds: float
    ) -> None:
        """
        Log analysis completed event.
        
        Args:
            user_id: User identifier
            filename: Name of the analyzed file
            verdict: Analysis verdict
            confidence: Confidence score
            duration_seconds: Time taken for analysis
        """
        details = {
            "filename": filename,
            "verdict": verdict,
            "confidence": confidence,
            "duration_seconds": duration_seconds
        }
        
        self._log_event(
            event_type="analysis_completed",
            user_id=user_id,
            details=details,
            status="success"
        )
    
    def log_analysis_failed(
        self,
        user_id: Optional[str],
        filename: str,
        error: str
    ) -> None:
        """
        Log analysis failed event.
        
        Args:
            user_id: User identifier
            filename: Name of the file
            error: Error message
        """
        details = {
            "filename": filename
        }
        
        self._log_event(
            event_type="analysis_failed",
            user_id=user_id,
            details=details,
            status="failure",
            error=error
        )
    
    def log_report_generated(
        self,
        user_id: Optional[str],
        filename: str,
        report_type: str,
        duration_seconds: float
    ) -> None:
        """
        Log report generated event.
        
        Args:
            user_id: User identifier
            filename: Name of the analyzed file
            report_type: Type of report (PDF, JSON, etc.)
            duration_seconds: Time taken to generate report
        """
        details = {
            "filename": filename,
            "report_type": report_type,
            "duration_seconds": duration_seconds
        }
        
        self._log_event(
            event_type="report_generated",
            user_id=user_id,
            details=details,
            status="success"
        )
    
    def log_auth_success(
        self,
        user_id: Optional[str],
        auth_method: str,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log successful authentication event.
        
        Args:
            user_id: User identifier
            auth_method: Authentication method (email, google, etc.)
            ip_address: IP address of the request
        """
        details = {
            "auth_method": auth_method,
            "ip_address": ip_address
        }
        
        self._log_event(
            event_type="auth_success",
            user_id=user_id,
            details=details,
            status="success"
        )
    
    def log_auth_failure(
        self,
        user_id: Optional[str],
        auth_method: str,
        reason: str,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log failed authentication event.
        
        Args:
            user_id: User identifier (if available)
            auth_method: Authentication method
            reason: Reason for failure
            ip_address: IP address of the request
        """
        details = {
            "auth_method": auth_method,
            "reason": reason,
            "ip_address": ip_address
        }
        
        self._log_event(
            event_type="auth_failure",
            user_id=user_id,
            details=details,
            status="failure"
        )
    
    def log_rate_limit_exceeded(
        self,
        user_id: Optional[str],
        endpoint: str,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log rate limit exceeded event.
        
        Args:
            user_id: User identifier (if available)
            endpoint: API endpoint that was rate limited
            ip_address: IP address of the request
        """
        details = {
            "endpoint": endpoint,
            "ip_address": ip_address
        }
        
        self._log_event(
            event_type="rate_limit_exceeded",
            user_id=user_id,
            details=details,
            status="failure"
        )
    
    def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str],
        details: Dict[str, Any],
        severity: str = "info"
    ) -> None:
        """
        Log generic security event.
        
        Args:
            event_type: Type of security event
            user_id: User identifier
            details: Event details
            severity: Event severity (info, warning, error, critical)
        """
        status_map = {
            "info": "success",
            "warning": "failure",
            "error": "failure",
            "critical": "failure"
        }
        
        self._log_event(
            event_type=event_type,
            user_id=user_id,
            details=details,
            status=status_map.get(severity, "success")
        )


# Global audit logger instance
audit_logger = AuditLogger()
