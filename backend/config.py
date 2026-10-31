import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv

# Locate project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file from backend or project root if present
load_dotenv(BASE_DIR / "backend" / ".env")
load_dotenv(BASE_DIR / ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "Analytix Club API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Supabase credentials (leave blank for local demo/development mode)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "super-secret-analytix-jwt-token-key-2026")
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # CORS allowed origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "*"
    ]
    
    # Local uploads path
    UPLOAD_DIR: Path = BASE_DIR / "frontend" / "assets" / "uploads"
    
    @property
    def is_supabase_configured(self) -> bool:
        """Returns True if real Supabase credentials are provided."""
        return bool(
            self.SUPABASE_URL 
            and self.SUPABASE_KEY 
            and not self.SUPABASE_URL.startswith("http://placeholder")
            and len(self.SUPABASE_KEY) > 20
        )

settings = Settings()

# Ensure local uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

