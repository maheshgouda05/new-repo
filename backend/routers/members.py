from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from backend.services.auth_service import require_member, get_current_user
from backend.database import db
from backend.models.user import UserProfileOut, UserProfileUpdate
from backend.models.registration import LeaderboardEntry

router = APIRouter(prefix="/api/members", tags=["Member Operations"])

@router.get("/me", response_model=UserProfileOut)
async def get_my_profile(current_user: dict = Depends(require_member)):
    """
    Retrieve the current logged-in member's profile.
    """
    fresh_profile = db.get_profile_by_id(current_user["id"])
    if not fresh_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfileOut(**fresh_profile)

@router.put("/me", response_model=UserProfileOut)
async def update_my_profile(
    payload: UserProfileUpdate, 
    current_user: dict = Depends(require_member)
):
    """
    Update personal profile information.
    Members are STRICTLY limited to updating safe fields:
    full_name, phone, department, year, skills, bio, profile_photo.
    Roles, teams, and points are protected and ignored here.
    """
    allowed_updates = {}
    if payload.full_name is not None:
        allowed_updates["full_name"] = payload.full_name.strip()
    if payload.phone is not None:
        allowed_updates["phone"] = payload.phone.strip()
    if payload.department is not None:
        allowed_updates["department"] = payload.department.strip()
    if payload.year is not None:
        allowed_updates["year"] = payload.year.strip()
    if payload.skills is not None:
        allowed_updates["skills"] = payload.skills.strip()
    if payload.bio is not None:
        allowed_updates["bio"] = payload.bio.strip()
    if payload.profile_photo is not None:
        allowed_updates["profile_photo"] = payload.profile_photo.strip()

    updated = db.update_profile(current_user["id"], allowed_updates)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    return UserProfileOut(**updated)

@router.get("/overview")
async def get_member_overview(current_user: dict = Depends(require_member)):
    """
    Returns metrics and summary data for the member dashboard.
    """
    user_id = current_user["id"]
    event_regs = db.list_user_event_registrations(user_id)
    hack_regs = db.list_user_hackathon_registrations(user_id)
    points = db.get_member_points(user_id)
    
    # Calculate rank
    leaderboard = db.get_leaderboard()
    user_rank = next((item["rank"] for item in leaderboard if item["member_id"] == user_id), len(leaderboard))

    # Pull upcoming events
    all_events = db.list_events(status="published", user_id=user_id)
    upcoming_events = all_events[:3]

    # Pull latest announcements
    latest_announcements = db.list_announcements(status="published")[:3]

    return {
        "member": UserProfileOut(**current_user),
        "total_points": points,
        "rank": user_rank,
        "registered_events_count": len(event_regs),
        "registered_hackathons_count": len(hack_regs),
        "team": current_user.get("team", "None"),
        "upcoming_events": upcoming_events,
        "latest_announcements": latest_announcements,
        "my_registrations": event_regs[:5]
    }

@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_club_leaderboard(current_user: dict = Depends(require_member)):
    """
    View the official Analytix Club Leaderboard with member rankings and points.
    All members can view, but only admins can award points.
    """
    leaderboard = db.get_leaderboard()
    return [LeaderboardEntry(**item) for item in leaderboard]

@router.get("/teams")
async def get_teams_overview():
    """
    Public/Member view: List members active in the Tech, Design, and MOC teams.
    """
    tech_members = db.list_profiles(team="Tech")
    design_members = db.list_profiles(team="Design")
    moc_members = db.list_profiles(team="MOC")

    return {
        "tech": [UserProfileOut(**m) for m in tech_members],
        "design": [UserProfileOut(**m) for m in design_members],
        "moc": [UserProfileOut(**m) for m in moc_members]
    }

