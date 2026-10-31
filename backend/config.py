import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List, Any
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
    
    # Supabase credentials (mandatory in production)
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # Server configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # CORS allowed origins (strictly defined, no wildcards in production)
    ALLOWED_ORIGINS: Any = os.getenv(
        "ALLOWED_ORIGINS", 
        "https://analytix-644w.onrender.com,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5500,http://127.0.0.1:5500"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        origins = []
        if isinstance(self.ALLOWED_ORIGINS, str):
            origins = [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]
        elif isinstance(self.ALLOWED_ORIGINS, (list, tuple)):
            origins = [str(o).strip() for o in self.ALLOWED_ORIGINS if str(o).strip()]
        else:
            origins = ["https://analytix-644w.onrender.com"]

        # Security: Strip wildcard origin in production mode
        if self.ENVIRONMENT == "production":
            origins = [o for o in origins if o != "*"]
            if not origins:
                origins = ["https://analytix-644w.onrender.com"]
        return origins
    
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

    def validate_production(self):
        """Strict pre-flight checks when running in production environment."""
        if self.ENVIRONMENT == "production":
            if not self.is_supabase_configured:
                raise ValueError(
                    "CRITICAL: SUPABASE_URL and SUPABASE_KEY environment variables are mandatory in production!"
                )
            if not self.SUPABASE_SERVICE_ROLE_KEY:
                raise ValueError(
                    "CRITICAL: SUPABASE_SERVICE_ROLE_KEY is required in production for secure administrative operations!"
                )
            if "*" in self.cors_origins:
                raise ValueError("CRITICAL: Wildcard CORS origin '*' is strictly prohibited in production!")

settings = Settings()

# Ensure local uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

