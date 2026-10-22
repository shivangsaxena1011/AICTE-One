"""
AICTE ONE: Unified Institution Intelligence, Approval, Compliance & Document Verification Platform
FastAPI Production Application Entrypoint
Enhanced with Security Headers, Individual Authentication, and RBAC
"""
import sys
import os
import time
from collections import defaultdict

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from contextlib import asynccontextmanager
import logging
import uuid
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.database import engine, Base, init_db
from backend.seed import seed_database

# Routers
from backend.routes.auth import router as auth_router
from backend.routes.institutions import router as institutions_router
from backend.routes.applications import router as applications_router
from backend.routes.evc import router as evc_router
from backend.routes.documents import router as documents_router
from backend.routes.compliance import router as compliance_router
from backend.routes.complaints import router as complaints_router
from backend.routes.tasks import router as tasks_router
from backend.routes.graph import router as graph_router
from backend.routes.copilot import router as copilot_router
from backend.routes.analytics import router as analytics_router
from backend.routes.notifications import router as notifications_router
from backend.routes.audit import router as audit_router
from backend.routes.workflows import router as workflows_router
from backend.routes.escalations import router as escalations_router
from backend.routes.system import router as system_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("aicte_one")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_database()
    yield

# Initialize FastAPI App
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Unified Institution Intelligence, Approval, Compliance & Document Verification Platform REST API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ---------------------------------------------------------------------------
# Structured Request Tracking & Telemetry Middleware (X-Request-ID)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def request_tracking_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"REQ-{uuid.uuid4().hex[:12].upper()}"
    request.state.request_id = request_id
    start_time = time.time()

    # Payload size enforcement (Section 4)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            cl = int(content_length)
            max_limit = 20 * 1024 * 1024 if "/upload" in request.url.path else 2 * 1024 * 1024
            if cl > max_limit:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Payload too large. Request body exceeds authorized limits.", "request_id": request_id}
                )
        except ValueError:
            pass

    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    # Structured telemetry logging (passwords, tokens, and PII are strictly omitted)
    client_ip = request.client.host if request.client else "unknown"
    if not request.url.path.startswith("/static"):
        logger.info(f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms) [IP: {client_ip}]")

    return response

# ---------------------------------------------------------------------------
# Rate Limiting & Throttling Middleware
# ---------------------------------------------------------------------------
RATE_LIMIT_STORE = defaultdict(list)
RATE_LIMITS = {
    "/api/auth/login": (10, 60),  # 10 attempts per minute
    "/api/auth/password-reset-request": (5, 60),  # 5 attempts per minute
    "/api/auth/password-reset-confirm": (5, 60),  # 5 attempts per minute
    "/api/institutions/search": (60, 60),  # 60 searches per minute
    "/api/institutions/verify": (60, 60),  # 60 verification queries per minute
    "/api/copilot/query": (30, 60),  # 30 AI copilot queries per minute
    "/api/documents/upload": (20, 60),  # 20 document uploads per minute
}

@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    if settings.ENVIRONMENT == "testing" or os.getenv("ENVIRONMENT") == "testing":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    if path in RATE_LIMITS:
        max_requests, window_seconds = RATE_LIMITS[path]
        now = time.time()
        key = f"{client_ip}:{path}"
        timestamps = [ts for ts in RATE_LIMIT_STORE[key] if now - ts < window_seconds]
        if len(timestamps) >= max_requests:
            request_id = getattr(request.state, "request_id", "UNKNOWN")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Too many requests; please retry shortly.",
                    "request_id": request_id
                }
            )
        timestamps.append(now)
        RATE_LIMIT_STORE[key] = timestamps

    response = await call_next(request)
    return response

# ---------------------------------------------------------------------------
# Global Exception Handler (Zero Internal Stack Leaks)
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", f"REQ-{uuid.uuid4().hex[:12].upper()}")
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "request_id": request_id}
        )
    logger.error(f"[{request_id}] Unhandled server exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please contact the platform administrator quoting the reference Request ID.",
            "request_id": request_id
        }
    )

# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# ---------------------------------------------------------------------------
# Register API Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(institutions_router)
app.include_router(applications_router)
app.include_router(evc_router)
app.include_router(documents_router)
app.include_router(compliance_router)
app.include_router(complaints_router)
app.include_router(tasks_router)
app.include_router(graph_router)
app.include_router(copilot_router)
app.include_router(analytics_router)
app.include_router(notifications_router)
app.include_router(audit_router)
app.include_router(workflows_router)
app.include_router(escalations_router)
app.include_router(system_router)

# Mount Frontend static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "aicte-one-prototype")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
def serve_frontend_root():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": settings.APP_NAME, "status": "Running", "docs": "/docs"}

@app.get("/index.html")
def serve_frontend_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": settings.APP_NAME, "status": "Running"}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected",
        "auth": "enforced"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
