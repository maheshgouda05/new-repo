from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

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
    access_token: str
    token_type: str = "bearer"
    user: UserProfileOut

