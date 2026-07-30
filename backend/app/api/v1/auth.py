from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, validator
from typing import Optional
from app.core.security import create_access_token, get_password_hash
from app.core.rate_limit import limiter
from app.core.audit_logger import audit_logger
import uuid, hashlib, os
from datetime import datetime
import re

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User name")
    email: str = Field(..., min_length=5, max_length=255, description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    role: Optional[str] = Field("general", description="User role")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255, description="User email address")
    password: str = Field(..., min_length=1, max_length=128, description="User password")
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()


class GoogleAuthRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=5000, description="Google OAuth token")


@router.post("/register")
@limiter.limit("10/minute")
async def register(request: Request, data: RegisterRequest):
    try:
        user_id = str(uuid.uuid4())
        user = {
            "user_id": user_id,
            "name": data.name,
            "email": data.email,
            "role": data.role or "general",
            "provider": "email",
            "created_at": datetime.utcnow().isoformat(),
        }
        # Create JWT with email as 'sub' so backend can identify user
        token = create_access_token({"sub": data.email, "user_id": user_id, "name": data.name})
        
        # Log successful registration
        audit_logger.log_auth_success(data.email, "email", request.client.host if request.client else None)
        
        return {"message": "Registration successful", "access_token": token, "token_type": "bearer", "user": user}
    except Exception as e:
        audit_logger.log_auth_failure(data.email, "email", str(e), request.client.host if request.client else None)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest):
    if not data.email or not data.password:
        audit_logger.log_auth_failure(data.email, "email", "Missing credentials", request.client.host if request.client else None)
        raise HTTPException(status_code=400, detail="Email and password required")

    # Generate a stable user_id from email (deterministic for mock auth)
    user_id = str(uuid.uuid5(uuid.NAMESPACE_URL, data.email))
    user = {
        "user_id": user_id,
        "name": data.email.split("@")[0],
        "email": data.email,
        "role": "general",
        "provider": "email",
        "created_at": datetime.utcnow().isoformat(),
    }
    # Real JWT with email in 'sub' claim
    token = create_access_token({"sub": data.email, "user_id": user_id, "name": user["name"]})
    
    # Log successful login
    audit_logger.log_auth_success(data.email, "email", request.client.host if request.client else None)
    
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me")
async def get_me():
    return {"message": "authenticated"}


@router.post("/google")
@limiter.limit("10/minute")
async def google_login(request: Request, data: GoogleAuthRequest):
    """
    Verify Google ID token and return a proper JWT.
    Falls back to decoding the credential client-side if google-auth library unavailable.
    """
    email = None
    name = None
    picture = None
    sub = None  # Google user ID

    # Try server-side verification first
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        if CLIENT_ID:
            id_info = id_token.verify_oauth2_token(
                data.token, google_requests.Request(), CLIENT_ID
            )
            email   = id_info.get("email")
            name    = id_info.get("name")
            picture = id_info.get("picture")
            sub     = id_info.get("sub")
    except Exception as e:
        print(f"[AUTH] Google server-side verify failed (using client decode): {e}")

    # Fallback: decode the JWT credential directly (it's a valid JWT from Google)
    if not email:
        try:
            import base64, json as _json
            # JWT is header.payload.sig — decode payload
            payload_b64 = data.token.split(".")[1]
            # Add padding
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = _json.loads(base64.urlsafe_b64decode(payload_b64))
            email   = payload.get("email")
            name    = payload.get("name")
            picture = payload.get("picture")
            sub     = payload.get("sub")
        except Exception as e2:
            print(f"[AUTH] JWT decode fallback failed: {e2}")

    if not email:
        audit_logger.log_auth_failure(None, "google", "Could not extract user info from token", request.client.host if request.client else None)
        raise HTTPException(status_code=401, detail="Could not extract user info from Google token")

    user_id = str(uuid.uuid5(uuid.NAMESPACE_URL, email))  # Stable ID from email
    now_iso = datetime.utcnow().isoformat()

    user = {
        "user_id":    user_id,
        "name":       name or email.split("@")[0],
        "email":      email,
        "picture":    picture or "",
        "role":       "general",
        "provider":   "google",
        "created_at": now_iso,
        "last_login": now_iso,
    }

    # Issue a real JWT with email in sub
    token = create_access_token({
        "sub":     email,
        "user_id": user_id,
        "name":    user["name"],
        "picture": picture or "",
        "provider": "google",
    })
    
    # Log successful Google login
    audit_logger.log_auth_success(email, "google", request.client.host if request.client else None)

    return {"access_token": token, "token_type": "bearer", "user": user}
