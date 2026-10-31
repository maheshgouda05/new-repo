from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from backend.services.auth_service import require_admin, get_optional_user
from backend.database import db
from backend.models.event import EventCreate, EventUpdate, EventOut
from backend.models.registration import RegistrationOut
from backend.services.storage_service import storage_service

router = APIRouter(prefix="/api/events", tags=["Events Management"])

@router.get("", response_model=List[EventOut])
async def list_events(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    List events.
    Public and members see only published/completed events.
    Admins can view drafts and all events.
    """
    is_admin = current_user and current_user.get("role") == "admin"
    user_id = current_user.get("id") if current_user else None

    # Non-admins can only see published events
    if not is_admin:
        effective_status = status_filter if status_filter in ["published", "completed"] else "published"
    else:
        effective_status = status_filter

    events = db.list_events(status=effective_status, user_id=user_id)
    return [EventOut(**e) for e in events]

@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get detailed information about a specific event.
    """
    user_id = current_user.get("id") if current_user else None
    event = db.get_event_by_id(event_id, user_id=user_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    is_admin = current_user and current_user.get("role") == "admin"
    if not is_admin and event.get("status") == "draft":
        raise HTTPException(status_code=404, detail="Event not found or not yet published")

    return EventOut(**event)

@router.post("", response_model=EventOut)
async def create_event(
    payload: EventCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new club event.
    Only authorized admins can create events.
    """
    event_dict = payload.model_dump()
    created = db.create_event(event_dict, created_by=current_user["id"])
    return EventOut(**created)

@router.post("/upload-poster")
async def upload_event_poster(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin)
):
    """
    Upload an event poster to Supabase Storage (posters bucket).
    Only authorized admins can upload event posters.
    """
    url = await storage_service.upload_file(file, bucket="posters")
    return {"url": url}

@router.put("/{event_id}", response_model=EventOut)
async def update_event(
    event_id: str,
    payload: EventUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Update an existing event.
    Only authorized admins can edit events.
    """
    existing = db.get_event_by_id(event_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")

    updates = payload.model_dump(exclude_unset=True)
    updated = db.update_event(event_id, updates)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update event")
    return EventOut(**updated)

@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete an event.
    Only authorized admins can delete events.
    """
    existing = db.get_event_by_id(event_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Event not found")

    success = db.delete_event(event_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete event")
    return {"message": "Event deleted successfully"}

@router.get("/{event_id}/registrations", response_model=List[RegistrationOut])
async def get_event_registrations(
    event_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    View all members registered for a specific event.
    Only authorized admins can view this list.
    """
    regs = db.list_all_event_registrations(event_id=event_id)
    return [RegistrationOut(**r) for r in regs]

