from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from backend.services.auth_service import require_admin
from backend.database import db
from backend.models.user import UserProfileOut, UserRoleUpdate, UserTeamUpdate
from backend.models.registration import LeaderboardAward, LeaderboardEntry

router = APIRouter(prefix="/api/admin", tags=["Admin Management"])

@router.get("/overview")
async def get_overview(current_user: dict = Depends(require_admin)):
    """
    Returns dashboard overview metrics:
    total registered members, total events, upcoming hackathons,
    total event registrations, and recent activities.
    """
    stats = db.get_overview_stats()
    return stats

@router.get("/members", response_model=List[UserProfileOut])
async def list_members(
    search: Optional[str] = Query(None, description="Search by name or email"),
    team: Optional[str] = Query(None, description="Filter by team (Tech, Design, MOC)"),
    role: Optional[str] = Query(None, description="Filter by role (admin, member)"),
    current_user: dict = Depends(require_admin)
):
    """
    List all club members with search and filter capabilities.
    """
    members = db.list_profiles(search=search, team=team, role=role)
    return [UserProfileOut(**m) for m in members]

@router.get("/members/{member_id}", response_model=UserProfileOut)
async def get_member_details(member_id: str, current_user: dict = Depends(require_admin)):
    """
    Get full profile details for a specific member.
    """
    profile = db.get_profile_by_id(member_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Member not found")
    return UserProfileOut(**profile)

@router.patch("/members/{member_id}/role", response_model=UserProfileOut)
async def update_member_role(
    member_id: str, 
    payload: UserRoleUpdate, 
    current_user: dict = Depends(require_admin)
):
    """
    Manage member role (promote to admin or demote to member).
    Only authorized admins can perform this action.
    """
    target = db.get_profile_by_id(member_id)
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    # Safety: Cannot demote yourself if you are the logged in admin
    if current_user["id"] == member_id and payload.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot revoke your own admin permissions."
        )

    updated = db.update_profile(member_id, {"role": payload.role})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update member role")
    return UserProfileOut(**updated)

@router.patch("/members/{member_id}/team", response_model=UserProfileOut)
async def assign_member_team(
    member_id: str, 
    payload: UserTeamUpdate, 
    current_user: dict = Depends(require_admin)
):
    """
    Assign a member to one of the club's 3 teams: Tech, Design, or MOC.
    """
    target = db.get_profile_by_id(member_id)
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    updated = db.update_profile(member_id, {"team": payload.team})
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to assign team")
    return UserProfileOut(**updated)

@router.post("/leaderboard/award")
async def award_points(
    payload: LeaderboardAward, 
    current_user: dict = Depends(require_admin)
):
    """
    Award activity points to a club member.
    Only admins have permission to award points.
    """
    target = db.get_profile_by_id(payload.member_id)
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")

    record = db.award_points(
        member_id=payload.member_id,
        points=payload.points,
        description=payload.activity_description.strip(),
        awarded_by=current_user["id"]
    )
    return {
        "message": f"Successfully awarded {payload.points} points to {target['full_name']}",
        "record": record
    }

