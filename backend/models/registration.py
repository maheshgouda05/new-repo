from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from backend.models.event import EventOut, HackathonOut
from backend.models.user import UserProfileOut

class EventRegistrationCreate(BaseModel):
    event_id: str

class HackathonRegistrationCreate(BaseModel):
    hackathon_id: str
    team_name: Optional[str] = ""

class RegistrationStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|approved|rejected|attended)$")

class HackathonStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(registered|shortlisted|participated|winner)$")

class RegistrationOut(BaseModel):
    id: str
    member_id: str
    event_id: str
    status: str
    registered_at: datetime
    member: Optional[UserProfileOut] = None
    event: Optional[EventOut] = None

class HackathonRegistrationOut(BaseModel):
    id: str
    member_id: str
    hackathon_id: str
    team_name: Optional[str] = ""
    status: str
    registered_at: datetime
    member: Optional[UserProfileOut] = None
    hackathon: Optional[HackathonOut] = None

class LeaderboardAward(BaseModel):
    member_id: str
    points: int = Field(..., gt=0)
    activity_description: str = Field(..., min_length=3)

class LeaderboardEntry(BaseModel):
    member_id: str
    full_name: str
    email: str
    department: Optional[str] = ""
    year: Optional[str] = ""
    team: Optional[str] = "None"
    profile_photo: Optional[str] = ""
    total_points: int
    activities_count: int
    rank: int

