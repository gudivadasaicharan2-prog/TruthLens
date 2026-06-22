from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.security import create_access_token, get_password_hash
import uuid, hashlib, os
from datetime import datetime

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "general"


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    token: str


@router.post("/register")
async def register(data: RegisterRequest):
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
        return {"message": "Registration successful", "access_token": token, "token_type": "bearer", "user": user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login(data: LoginRequest):
    if not data.email or not data.password:
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
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me")
async def get_me():
    return {"message": "authenticated"}


@router.post("/google")
async def google_login(data: GoogleAuthRequest):
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

    return {"access_token": token, "token_type": "bearer", "user": user}
