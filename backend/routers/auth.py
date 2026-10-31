import logging
import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from backend.models.user import UserRegister, UserLogin, TokenResponse, UserProfileOut
from backend.database import db, store, supabase_client
from backend.services.auth_service import auth_service, get_current_user
from backend.config import settings

logger = logging.getLogger("analytix.auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(payload: UserRegister):
    """
    Register a new club member account.
    All new registrations are strictly assigned the 'member' role.
    Uses Supabase Auth and persists user profile.
    """
    clean_email = payload.email.strip().lower()

    # Pre-check existing profile in database
    existing_user = db.get_profile_by_email(clean_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )

    user_dict = {
        "email": clean_email,
        "full_name": payload.full_name.strip(),
        "phone": (payload.phone or "").strip(),
        "department": (payload.department or "").strip(),
        "year": (payload.year or "").strip(),
        "skills": (payload.skills or "").strip(),
        "bio": (payload.bio or "").strip(),
        "role": "member",  # Security: Always force role to member
        "team": "None"
    }

    token = None
    created_profile = None

    if supabase_client and settings.is_supabase_configured:
        user_id = None
        try:
            # First attempt: Admin create_user (avoids email confirmation rate limits on college networks)
            if settings.SUPABASE_SERVICE_ROLE_KEY:
                try:
                    admin_res = supabase_client.auth.admin.create_user({
                        "email": clean_email,
                        "password": payload.password,
                        "email_confirm": True,
                        "user_metadata": {
                            "full_name": payload.full_name,
                            "role": "member"
                        }
                    })
                    if admin_res and admin_res.user:
                        user_id = admin_res.user.id
                except Exception as admin_err:
                    err_msg = str(admin_err).lower()
                    if "already" in err_msg or "exists" in err_msg:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="An account with this email address already exists. Please log in."
                        )
                    logger.debug(f"Admin create_user fallback to sign_up: {admin_err}")

            # Fallback attempt: Standard sign_up if admin create was unavailable
            if not user_id:
                auth_response = supabase_client.auth.sign_up({
                    "email": clean_email,
                    "password": payload.password,
                    "options": {
                        "data": {
                            "full_name": payload.full_name,
                            "role": "member"
                        }
                    }
                })
                if not auth_response.user:
                    raise HTTPException(status_code=400, detail="Supabase registration failed.")
                user_id = auth_response.user.id

            user_dict["id"] = user_id
            created_profile = db.create_user(user_dict, "")

            # Acquire valid Supabase-issued session token
            try:
                auth_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
                login_resp = httpx.post(
                    auth_url,
                    headers={"apikey": settings.SUPABASE_KEY, "Content-Type": "application/json"},
                    json={"email": clean_email, "password": payload.password},
                    timeout=10.0
                )
                if login_resp.status_code == 200:
                    token = login_resp.json().get("access_token")
            except Exception as sign_in_err:
                logger.warning(f"Immediate sign_in after registration notice: {sign_in_err}")

            if not token:
                if settings.ENVIRONMENT == "production":
                    raise HTTPException(
                        status_code=status.HTTP_201_CREATED,
                        detail="Registration successful! Please confirm your email before signing in."
                    )
                token = auth_service.create_access_token({"sub": user_id, "email": clean_email})

        except HTTPException:
            raise
        except Exception as e:
            err_str = str(e)
            logger.error(f"Supabase auth registration error: {err_str}")
            if "already" in err_str.lower() or "unique" in err_str.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="An account with this email address already exists. Please log in."
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_str)
    else:
        # Development / local mode fallback only
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Production authentication service is currently unavailable. Supabase connection required."
            )
        pwd_hash = db.hash_password(payload.password)
        created_profile = db.create_user(user_dict, pwd_hash)
        token = auth_service.create_access_token({
            "sub": created_profile["id"],
            "email": created_profile["email"]
        })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileOut(**created_profile)
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    """
    Authenticate a user via email and password using Supabase Authentication.
    Validates credentials, retrieves authoritative role from profiles table,
    and returns session access token.
    """
    email_clean = payload.email.strip().lower()
    
    if supabase_client and settings.is_supabase_configured:
        try:
            auth_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/token?grant_type=password"
            resp = httpx.post(
                auth_url,
                headers={"apikey": settings.SUPABASE_KEY, "Content-Type": "application/json"},
                json={"email": email_clean, "password": payload.password},
                timeout=10.0
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password. Please verify your credentials."
                )
            auth_data = resp.json()
            user_info = auth_data.get("user") or {}
            user_id = user_info.get("id")
            token = auth_data.get("access_token")
            
            if not user_id or not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password. Please verify your credentials."
                )

            # Authoritative role and profile retrieval from profiles table
            user_profile = db.get_profile_by_id(user_id) or db.get_profile_by_email(email_clean)
            if not user_profile:
                # If profile trigger was delayed, auto-populate initial profile
                user_profile = db.create_user({
                    "id": user_id,
                    "email": email_clean,
                    "full_name": email_clean.split("@")[0],
                    "role": "member",
                    "team": "None"
                }, "")
            
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=UserProfileOut(**user_profile)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Supabase sign in failed for {email_clean}: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid email or password. Please verify your credentials."
            )

    # In production, local demo authentication is strictly prohibited
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Production authentication service is currently unavailable. Supabase connection required."
        )

    # Local development fallback
    profile = db.get_profile_by_email(email_clean)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email address. Please register first."
        )

    user_id = profile["id"]
    hashed_pwd = store.passwords.get(user_id)
    if not hashed_pwd or not db.verify_password(payload.password, hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please verify and try again."
        )

    token = auth_service.create_access_token({
        "sub": user_id,
        "email": profile["email"]
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileOut(**profile)
    )

@router.get("/me", response_model=UserProfileOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile and verified role.
    """
    return UserProfileOut(**current_user)

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Invalidates user session.
    """
    return {"message": "Successfully logged out"}
