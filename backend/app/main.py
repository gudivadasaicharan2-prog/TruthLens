from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Force UTF-8 on Windows consoles (prevents charmap/cp1252 UnicodeEncodeError
# when print() outputs non-ASCII characters during request handling)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass  # Python < 3.7 or non-reconfigurable stream

app = FastAPI(
    title="TruthLens API",
    version="2.0.0",
    description="AI Content Authenticity & Deepfake Detection Platform"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload dirs
for d in ["./uploads/images", "./uploads/videos",
          "./uploads/audio", "./uploads/frames"]:
    os.makedirs(d, exist_ok=True)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "TruthLens API v2 running",
        "version": "2.0.0",
        "platform": "AI Content Authenticity & Deepfake Detection"
    }

# Register routers safely
def register(module_path, prefix, tag):
    try:
        import importlib
        module = importlib.import_module(module_path)
        app.include_router(module.router, prefix=prefix, tags=[tag])
        print(f"[OK] {tag} router registered at {prefix}")
    except Exception as e:
        print(f"[ERROR] {tag} router failed: {e}")

register("app.api.v1.auth",      "/api/v1/auth",      "Auth")
register("app.api.v1.image",     "/api/v1/image",     "Image")
register("app.api.v1.video",     "/api/v1/video",     "Video")
register("app.api.v1.audio",     "/api/v1/audio",     "Audio")
register("app.api.v1.dashboard", "/api/v1/users", "Dashboard")
register("app.api.v1.users",     "/api/v1/users",     "Users")
register("app.api.v1.health",    "/api/v1/health",    "Health")
# NOTE: news and factcheck routes removed — platform is now media-only (ASCII safe comment)
