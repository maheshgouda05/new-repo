from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- EVENTS ---
class EventBase(BaseModel):
    title: str = Field(..., min_length=2)
    description: str
    venue: str
    event_date: datetime
    registration_deadline: datetime
    instructions: Optional[str] = ""
    status: Optional[str] = "published"  # draft, published, completed, cancelled
    poster_url: Optional[str] = ""
    photos: Optional[List[str]] = []

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    venue: Optional[str] = None
    event_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    poster_url: Optional[str] = None
    photos: Optional[List[str]] = None

class EventOut(EventBase):
    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    registrations_count: Optional[int] = 0
    is_registered: Optional[bool] = False
    my_registration_status: Optional[str] = None

# --- HACKATHONS ---
class HackathonBase(BaseModel):
    title: str = Field(..., min_length=2)
    organizer: str
    description: str
    start_date: datetime
    deadline: datetime
    location: str
    mode: str = "online"  # online, offline, hybrid
    registration_link: Optional[str] = ""
    eligibility: Optional[str] = "All college students"
    required_skills: Optional[str] = ""
    status: Optional[str] = "published"  # draft, published, completed, cancelled
    poster_url: Optional[str] = ""

class HackathonCreate(HackathonBase):
    pass

class HackathonUpdate(BaseModel):
    title: Optional[str] = None
    organizer: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    location: Optional[str] = None
    mode: Optional[str] = None
    registration_link: Optional[str] = None
    eligibility: Optional[str] = None
    required_skills: Optional[str] = None
    status: Optional[str] = None
    poster_url: Optional[str] = None

class HackathonOut(HackathonBase):
    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    is_registered: Optional[bool] = False
    my_registration_status: Optional[str] = None

# --- ANNOUNCEMENTS ---
class AnnouncementBase(BaseModel):
    title: str = Field(..., min_length=2)
    description: str
    category: Optional[str] = "General"  # General, Notice, Urgent, Opportunity, Event
    image_url: Optional[str] = ""
    status: Optional[str] = "published"  # draft, published, archived

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

class AnnouncementOut(AnnouncementBase):
    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

