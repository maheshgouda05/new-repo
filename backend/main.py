import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.config import settings, BASE_DIR
from backend.routers import auth, admin, members, events, hackathons, announcements, registrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("analytix")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Analytix Club - College Technical & Data Science Club"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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

# Health Check Endpoint
@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "supabase_configured": settings.is_supabase_configured,
        "mode": "production" if settings.is_supabase_configured else "development/fallback"
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

