import logging
import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from backend.models.user import (
    UserRegister, 
    UserLogin, 
    TokenResponse, 
    UserProfileOut,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    PhoneSendOtpRequest,
    PhoneVerifyOtpRequest,
    normalize_phone_number
)
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
    Uses Supabase Auth and persists member profile.
    """
    clean_email = payload.email.strip().lower()
    clean_phone = normalize_phone_number(payload.phone)

    # 1. Pre-check existing email in database
    existing_user = db.get_profile_by_email(clean_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )

    # 2. Pre-check existing phone in database
    if clean_phone:
        existing_phone_user = db.get_profile_by_phone(clean_phone)
        if existing_phone_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This phone number is already registered to another member account. Please use a different phone number or sign in."
            )

    user_dict = {
        "email": clean_email,
        "full_name": payload.full_name.strip(),
        "phone": clean_phone,
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
            # First attempt: Admin create_user (auto-confirms to prevent email rate limits)
            if settings.SUPABASE_SERVICE_ROLE_KEY:
                try:
                    admin_create_payload = {
                        "email": clean_email,
                        "password": payload.password,
                        "email_confirm": True,
                        "user_metadata": {
                            "full_name": payload.full_name.strip(),
                            "role": "member"
                        }
                    }
                    if clean_phone:
                        admin_create_payload["phone"] = clean_phone
                        admin_create_payload["phone_confirm"] = True

                    admin_res = supabase_client.auth.admin.create_user(admin_create_payload)
                    if admin_res and admin_res.user:
                        user_id = admin_res.user.id
                except Exception as admin_err:
                    err_msg = str(admin_err).lower()
                    if "already" in err_msg or "exists" in err_msg or "unique" in err_msg:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="An account with this email or phone number already exists in Supabase. Please log in."
                        )
                    logger.debug(f"Admin create_user fallback to sign_up: {admin_err}")

            # Fallback attempt: Standard sign_up if admin create was unavailable
            if not user_id:
                auth_response = supabase_client.auth.sign_up({
                    "email": clean_email,
                    "password": payload.password,
                    "options": {
                        "data": {
                            "full_name": payload.full_name.strip(),
                            "role": "member"
                        }
                    }
                })
                if not auth_response.user:
                    raise HTTPException(status_code=400, detail="Supabase registration failed. Please try again.")
                user_id = auth_response.user.id

            user_dict["id"] = user_id
            created_profile = db.create_user(user_dict, "")

            # Attempt to acquire a live Supabase session token via password grant
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

            # If Supabase email confirmation is enabled and no session is returned:
            # DO NOT generate a fake session. Inform user to verify their email.
            if not token:
                return TokenResponse(
                    access_token=None,
                    token_type="bearer",
                    user=UserProfileOut(**created_profile),
                    requires_verification=True,
                    message="Account created successfully! Please check your email inbox to verify your account before logging in."
                )

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
        user=UserProfileOut(**created_profile),
        requires_verification=False,
        message="Registration successful! Welcome to Analytix Club."
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    """
    Authenticate a user via email and password using Supabase Authentication.
    Validates credentials, retrieves authoritative role from profiles table,
    and returns session access token.
    Provides clear, informative error messages for unconfirmed emails vs wrong passwords.
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
                err_data = {}
                try:
                    err_data = resp.json()
                except Exception:
                    pass

                err_code = str(err_data.get("error_code") or err_data.get("error") or "")
                err_msg = str(err_data.get("msg") or err_data.get("error_description") or "")

                if "email_not_confirmed" in err_code or "Email not confirmed" in err_msg:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Your email has not been confirmed yet. Please check your inbox for the confirmation link before signing in."
                    )
                elif "invalid_credentials" in err_code or "invalid_grant" in err_code:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid email or password. Please verify your credentials."
                    )
                elif resp.status_code == 429:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many sign in attempts. Please wait a few minutes before trying again."
                    )
                else:
                    detail_text = err_msg or "Invalid email or password. Please verify your credentials."
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail_text)

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
                user=UserProfileOut(**user_profile),
                requires_verification=False,
                message=f"Welcome back, {user_profile['full_name']}!"
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
        user=UserProfileOut(**profile),
        requires_verification=False,
        message=f"Welcome back, {profile['full_name']}!"
    )

# --- FORGOT & RESET PASSWORD ---

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """
    Sends a password recovery email using Supabase Auth.
    Security: Does not reveal whether the email exists.
    """
    clean_email = payload.email.strip().lower()

    if supabase_client and settings.is_supabase_configured:
        try:
            recover_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/recover"
            httpx.post(
                recover_url,
                headers={"apikey": settings.SUPABASE_KEY, "Content-Type": "application/json"},
                json={"email": clean_email},
                timeout=10.0
            )
        except Exception as e:
            logger.error(f"Supabase password recover request failed: {e}")

    return {
        "status": "success",
        "message": "Password reset link has been sent. Please check your email inbox (and spam folder)."
    }

@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates the authenticated user's password using their active recovery session.
    """
    user_id = current_user["id"]

    if supabase_client and settings.is_supabase_configured:
        try:
            if settings.SUPABASE_SERVICE_ROLE_KEY:
                supabase_client.auth.admin.update_user_by_id(user_id, {"password": payload.new_password})
            else:
                raise HTTPException(status_code=500, detail="Service role key required to update password.")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resetting password for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update password. Recovery link may have expired."
            )
    else:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(status_code=503, detail="Supabase connection required.")
        store.passwords[user_id] = db.hash_password(payload.new_password)

    return {
        "status": "success",
        "message": "Your password has been successfully updated. Please log in with your new password."
    }

# --- PHONE NUMBER LOGIN USING OTP ---

@router.post("/phone/send-otp")
async def send_phone_otp(payload: PhoneSendOtpRequest):
    """
    Sends an SMS OTP to a registered club member's mobile phone number.
    Strictly prevents sending OTPs to unregistered numbers (does not create member accounts on login).
    """
    clean_phone = normalize_phone_number(payload.phone)
    if not clean_phone or len(clean_phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid phone number with country code (e.g., +919876543210)."
        )

    # 1. Enforce: Phone number MUST be linked to an existing registered profile
    profile = db.get_profile_by_phone(clean_phone)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No club member account is registered with this phone number. Please register first or sign in using your email address."
        )

    if not supabase_client or not settings.is_supabase_configured:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(status_code=503, detail="Supabase phone authentication is not configured.")
        return {
            "message": f"OTP sent to {clean_phone} (Dev test mode: use code 123456).",
            "phone": clean_phone,
            "cooldown": 60
        }

    try:
        otp_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/otp"
        resp = httpx.post(
            otp_url,
            headers={"apikey": settings.SUPABASE_KEY, "Content-Type": "application/json"},
            json={"phone": clean_phone, "create_user": False},
            timeout=10.0
        )
        res_data = resp.json() if resp.content else {}

        if resp.status_code != 200:
            err_code = str(res_data.get("error_code") or "")
            err_msg = str(res_data.get("msg") or "Failed to send OTP.")

            if err_code == "phone_provider_disabled" or "Unsupported phone provider" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone/SMS authentication is currently disabled in your Supabase project. Please enable Phone provider under Authentication -> Providers -> Phone in your Supabase Dashboard."
                )
            elif resp.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many OTP requests. Please wait a minute before requesting another code."
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

        return {
            "message": f"OTP successfully sent to {clean_phone}.",
            "phone": clean_phone,
            "cooldown": 60
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending phone OTP: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/phone/verify-otp", response_model=TokenResponse)
async def verify_phone_otp(payload: PhoneVerifyOtpRequest):
    """
    Verifies phone OTP with Supabase Auth and returns an authentic Supabase session.
    Retrieves the authoritative user profile and role from the database.
    """
    clean_phone = normalize_phone_number(payload.phone)
    clean_otp = payload.otp.strip()

    # Authoritative check: profile must exist for this phone number
    profile = db.get_profile_by_phone(clean_phone)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered member account was found with this phone number."
        )

    if not supabase_client or not settings.is_supabase_configured:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(status_code=503, detail="Supabase phone authentication is not configured.")
        if clean_otp != "123456":
            raise HTTPException(status_code=400, detail="Invalid OTP code. Dev test code is 123456.")
        token = auth_service.create_access_token({"sub": profile["id"], "email": profile["email"]})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserProfileOut(**profile),
            requires_verification=False,
            message=f"Welcome back, {profile['full_name']}!"
        )

    try:
        verify_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/verify"
        resp = httpx.post(
            verify_url,
            headers={"apikey": settings.SUPABASE_KEY, "Content-Type": "application/json"},
            json={"type": "sms", "phone": clean_phone, "token": clean_otp},
            timeout=10.0
        )
        res_data = resp.json() if resp.content else {}

        if resp.status_code != 200:
            err_msg = res_data.get("msg") or res_data.get("error_description") or "Invalid or expired OTP."
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

        token = res_data.get("access_token")
        user_data = res_data.get("user") or {}
        user_id = user_data.get("id") or profile["id"]

        # Retrieve authoritative profile by ID or phone
        live_profile = db.get_profile_by_id(user_id) or profile

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserProfileOut(**live_profile),
            requires_verification=False,
            message=f"Welcome back, {live_profile['full_name']}!"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying phone OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please try again."
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
