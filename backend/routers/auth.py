import logging
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
    """
    existing_user = db.get_profile_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )

    user_dict = {
        "email": payload.email.strip().lower(),
        "full_name": payload.full_name.strip(),
        "phone": payload.phone or "",
        "department": payload.department or "",
        "year": payload.year or "",
        "skills": payload.skills or "",
        "bio": payload.bio or "",
        "role": "member",  # Security: Always force role to member
        "team": "None"
    }

    token = None
    created_profile = None

    if supabase_client and settings.is_supabase_configured:
        try:
            # Sign up user with Supabase Auth
            auth_response = supabase_client.auth.sign_up({
                "email": payload.email,
                "password": payload.password,
                "options": {
                    "data": {
                        "full_name": payload.full_name,
                        "phone": payload.phone,
                        "department": payload.department,
                        "year": payload.year,
                        "skills": payload.skills,
                        "bio": payload.bio
                    }
                }
            })
            if not auth_response.user:
                raise HTTPException(status_code=400, detail="Supabase registration failed.")
            
            user_id = auth_response.user.id
            user_dict["id"] = user_id
            created_profile = db.create_user(user_dict, "")
            token = auth_response.session.access_token if auth_response.session else auth_service.create_access_token({
                "sub": user_id,
                "email": payload.email
            })
        except Exception as e:
            logger.error(f"Supabase auth error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Fallback local registration
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
    Authenticate a user via email and password.
    Returns session token and verified profile with role.
    """
    email_clean = payload.email.strip().lower()
    
    if supabase_client and settings.is_supabase_configured:
        try:
            auth_res = supabase_client.auth.sign_in_with_password({
                "email": email_clean,
                "password": payload.password
            })
            if not auth_res.user:
                raise HTTPException(status_code=401, detail="Invalid email or password.")
            
            user_profile = db.get_profile_by_id(auth_res.user.id) or db.get_profile_by_email(email_clean)
            if not user_profile:
                # If trigger delayed, fetch or create minimal
                user_profile = db.get_profile_by_email(email_clean)
            
            token = auth_res.session.access_token
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=UserProfileOut(**user_profile)
            )
        except Exception as e:
            logger.error(f"Supabase sign in failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Fallback local authentication
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
    if supabase_client and settings.is_supabase_configured:
        try:
            supabase_client.auth.sign_out()
        except Exception:
            pass
    return {"message": "Successfully logged out"}

