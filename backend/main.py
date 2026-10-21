"""
AICTE ONE: Unified Institution Intelligence, Approval, Compliance & Document Verification Platform
FastAPI Production Application Entrypoint
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.database import engine, Base
from backend.seed import seed_database

# Routers
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
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

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
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
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
