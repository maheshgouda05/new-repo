from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from backend.config import settings
from backend.database import db, supabase_client

security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

class AuthService:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SUPABASE_JWT_SECRET, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Validates JWT token. If Supabase is connected, it verifies either
        via Supabase Auth API or JWT secret. In fallback mode, it verifies via JWT secret.
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SUPABASE_JWT_SECRET, 
                algorithms=[ALGORITHM],
                options={"verify_aud": False}
            )
            return payload
        except JWTError:
            # If Supabase Auth is enabled, also check supabase.auth.get_user(token)
            if supabase_client and settings.is_supabase_configured:
                try:
                    user_resp = supabase_client.auth.get_user(token)
                    if user_resp and user_resp.user:
                        return {"sub": user_resp.user.id, "email": user_resp.user.email}
                except Exception:
                    return None
            return None

auth_service = AuthService()

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Core authentication dependency.
    Extracts Bearer token, validates it, and fetches the user's authoritative
    profile from the database to strictly determine their role.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("id")
    email = payload.get("email")

    user_profile = None
    if user_id:
        user_profile = db.get_profile_by_id(user_id)
    if not user_profile and email:
        user_profile = db.get_profile_by_email(email)

    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or removed from database.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_profile

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Strict Admin Authorization Dependency.
    Verifies that the authenticated user possesses the 'admin' role in the database.
    Rejects normal members with 403 Forbidden.
    """
    role = current_user.get("role", "member")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin authorization required."
        )
    return current_user

async def require_member(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Verifies that the user is authenticated (member or admin).
    """
    return current_user

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Dependency for public routes that want to tailor content if a user happens to be logged in.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

