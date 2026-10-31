import re
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

def normalize_phone_number(phone: Optional[str]) -> str:
    """
    Normalizes phone numbers to standard international format (e.g., +919876543210).
    """
    if not phone:
        return ""
    cleaned = re.sub(r"[\s\-\(\)]", "", str(phone).strip())
    if not cleaned:
        return ""
    if cleaned.startswith("+"):
        digits = re.sub(r"[^\d]", "", cleaned[1:])
        return f"+{digits}" if digits else ""
    digits = re.sub(r"[^\d]", "", cleaned)
    if len(digits) == 10:
        return f"+91{digits}"
    elif len(digits) == 11 and digits.startswith("0"):
        return f"+91{digits[1:]}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+{digits}"
    return f"+{digits}" if digits else ""

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = ""
    department: Optional[str] = ""
    year: Optional[str] = ""
    skills: Optional[str] = ""
    bio: Optional[str] = ""

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=6)

class PhoneSendOtpRequest(BaseModel):
    phone: str = Field(..., min_length=8)

class PhoneVerifyOtpRequest(BaseModel):
    phone: str = Field(..., min_length=8)
    otp: str = Field(..., min_length=4, max_length=10)

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    year: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None
    profile_photo: Optional[str] = None

class UserRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(admin|member)$")

class UserTeamUpdate(BaseModel):
    team: str = Field(..., pattern="^(None|Tech|Design|MOC)$")

class UserProfileOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = ""
    profile_photo: Optional[str] = ""
    department: Optional[str] = ""
    year: Optional[str] = ""
    skills: Optional[str] = ""
    bio: Optional[str] = ""
    role: str
    team: str
    points: Optional[int] = 0
    created_at: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserProfileOut] = None
    requires_verification: bool = False
    message: Optional[str] = None

