from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from backend.services.auth_service import require_member, require_admin
from backend.database import db
from backend.models.registration import (
    RegistrationOut, 
    HackathonRegistrationOut, 
    RegistrationStatusUpdate,
    HackathonRegistrationCreate
)

router = APIRouter(prefix="/api/registrations", tags=["Registrations"])

@router.post("/events/{event_id}", response_model=RegistrationOut)
async def register_for_event(
    event_id: str,
    current_user: dict = Depends(require_member)
):
    """
    Register the logged-in member for an event.
    Enforces duplicate registration checks.
    """
    event = db.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    if event.get("status") not in ["published"]:
        raise HTTPException(status_code=400, detail="This event is not open for registration.")

    # Check if already registered
    existing = db.get_registration(current_user["id"], event_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already registered for this event."
        )

    reg = db.register_for_event(current_user["id"], event_id)
    reg["member"] = current_user
    reg["event"] = event
    return RegistrationOut(**reg)

@router.delete("/events/{event_id}")
async def cancel_event_registration(
    event_id: str,
    current_user: dict = Depends(require_member)
):
    """
    Cancel registration for an event.
    """
    existing = db.get_registration(current_user["id"], event_id)
    if not existing:
        raise HTTPException(status_code=404, detail="You are not registered for this event.")

    db.cancel_event_registration(current_user["id"], event_id)
    return {"message": "Registration cancelled successfully"}

@router.post("/hackathons/{hackathon_id}", response_model=HackathonRegistrationOut)
async def register_for_hackathon(
    hackathon_id: str,
    payload: Optional[HackathonRegistrationCreate] = None,
    current_user: dict = Depends(require_member)
):
    """
    Apply internally for a hackathon.
    Prevents duplicate registration.
    """
    hackathon = db.get_hackathon_by_id(hackathon_id)
    if not hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    existing = db.get_hackathon_registration(current_user["id"], hackathon_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied for this hackathon."
        )

    team_name = payload.team_name if payload else ""
    reg = db.register_for_hackathon(current_user["id"], hackathon_id, team_name=team_name)
    reg["member"] = current_user
    reg["hackathon"] = hackathon
    return HackathonRegistrationOut(**reg)

@router.get("/my")
async def get_my_registrations(current_user: dict = Depends(require_member)):
    """
    Returns all event and hackathon registrations for the current member.
    """
    user_id = current_user["id"]
    event_regs = db.list_user_event_registrations(user_id)
    hackathon_regs = db.list_user_hackathon_registrations(user_id)

    return {
        "events": event_regs,
        "hackathons": hackathon_regs
    }

@router.get("/admin/all", response_model=List[RegistrationOut])
async def list_all_registrations(current_user: dict = Depends(require_admin)):
    """
    Admin: View all event registrations across the club.
    """
    regs = db.list_all_event_registrations()
    return [RegistrationOut(**r) for r in regs]

@router.patch("/events/{registration_id}/status", response_model=RegistrationOut)
async def update_registration_status(
    registration_id: str,
    payload: RegistrationStatusUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Admin: Update registration status (pending, approved, rejected, attended).
    """
    updated = db.update_registration_status(registration_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Registration record not found")

    updated["member"] = db.get_profile_by_id(updated["member_id"])
    updated["event"] = db.get_event_by_id(updated["event_id"])
    return RegistrationOut(**updated)

