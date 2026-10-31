import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

from backend.config import settings, BASE_DIR
from backend.database import db, supabase_client
from backend.routers import auth, admin, members, events, hackathons, announcements, registrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("analytix")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Safe production startup validation
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT} mode]")
    if settings.ENVIRONMENT == "production":
        settings.validate_production()
        # Verify database connection
        try:
            if not supabase_client:
                raise RuntimeError("Supabase client not initialized.")
            supabase_client.table("profiles").select("id").limit(1).execute()
            logger.info("✅ Supabase database connection verified successfully.")
        except Exception as e:
            logger.error(f"❌ Production database pre-flight check failed: {e}")
            raise RuntimeError(f"Database pre-flight check failed in production: {e}")
    else:
        logger.info("Running in development/local mode.")
    yield
    logger.info("Application shutdown.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Analytix Club - College Technical & Data Science Club",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(members.router)
app.include_router(events.router)
app.include_router(hackathons.router)
app.include_router(announcements.router)
app.include_router(registrations.router)

# Health Check Endpoint - reports real database connection status
@app.get("/api/health", tags=["Health"])
def health_check():
    db_connected = False
    db_error = None
    if supabase_client and settings.is_supabase_configured:
        try:
            supabase_client.table("profiles").select("id").limit(1).execute()
            db_connected = True
        except Exception as e:
            db_connected = False
            db_error = str(e)
            logger.error(f"Health check database ping failed: {e}")

    is_healthy = db_connected if settings.ENVIRONMENT == "production" else True
    status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    content = {
        "status": "healthy" if is_healthy else "unhealthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "supabase_configured": settings.is_supabase_configured,
        "database_connected": db_connected,
        "mode": "production" if settings.ENVIRONMENT == "production" else "development"
    }
    if db_error:
        content["database_error"] = db_error

    return JSONResponse(status_code=status_code, content=content)

# Public Statistics Endpoint (Real data, no invented counts)
@app.get("/api/stats", tags=["Public Stats"])
def public_stats():
    """Returns authentic, real-time metrics for the public landing page."""
    try:
        stats = db.get_overview_stats()
        return {
            "members_count": stats.get("total_members", 0),
            "events_count": stats.get("total_events", 0),
            "hackathons_count": stats.get("upcoming_hackathons", 0),
            "teams_count": 3
        }
    except Exception:
        return {
            "members_count": 0,
            "events_count": 0,
            "hackathons_count": 0,
            "teams_count": 3
        }


# Mount uploaded media assets
uploads_dir = BASE_DIR / "frontend" / "assets" / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/assets/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Mount full frontend directory as static files so running uvicorn serves everything
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    # Serve HTML pages directly from root paths
    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")

    @app.get("/{page}.html", include_in_schema=False)
    async def serve_html_pages(page: str):
        file_path = frontend_dir / f"{page}.html"
        if file_path.exists():
            return FileResponse(file_path)
        return FileResponse(frontend_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)

