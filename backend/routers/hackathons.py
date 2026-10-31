from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from backend.services.auth_service import require_admin, get_optional_user
from backend.database import db
from backend.models.event import HackathonCreate, HackathonUpdate, HackathonOut
from backend.services.storage_service import storage_service

router = APIRouter(prefix="/api/hackathons", tags=["Hackathons Management"])

@router.get("", response_model=List[HackathonOut])
async def list_hackathons(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    List hackathons.
    Public and members see only published/active hackathons.
    Admins can view drafts and all hackathons.
    """
    is_admin = current_user and current_user.get("role") == "admin"
    user_id = current_user.get("id") if current_user else None

    if not is_admin:
        effective_status = status_filter if status_filter in ["published", "completed"] else "published"
    else:
        effective_status = status_filter

    hackathons = db.list_hackathons(status=effective_status, user_id=user_id)
    return [HackathonOut(**h) for h in hackathons]

@router.get("/{hackathon_id}", response_model=HackathonOut)
async def get_hackathon(
    hackathon_id: str,
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    Get detailed information about a specific hackathon.
    """
    user_id = current_user.get("id") if current_user else None
    hackathon = db.get_hackathon_by_id(hackathon_id, user_id=user_id)
    if not hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    is_admin = current_user and current_user.get("role") == "admin"
    if not is_admin and hackathon.get("status") == "draft":
        raise HTTPException(status_code=404, detail="Hackathon not found or not yet published")

    return HackathonOut(**hackathon)

@router.post("", response_model=HackathonOut)
async def create_hackathon(
    payload: HackathonCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new hackathon entry.
    Only authorized admins can add hackathons.
    """
    h_dict = payload.model_dump()
    created = db.create_hackathon(h_dict, created_by=current_user["id"])
    return HackathonOut(**created)

@router.post("/upload-poster")
async def upload_hackathon_poster(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin)
):
    """
    Upload a hackathon poster to Supabase Storage (posters bucket).
    Only authorized admins can upload posters.
    """
    url = await storage_service.upload_file(file, bucket="posters")
    return {"url": url}

@router.put("/{hackathon_id}", response_model=HackathonOut)
async def update_hackathon(
    hackathon_id: str,
    payload: HackathonUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Update an existing hackathon.
    Only authorized admins can edit hackathons.
    """
    existing = db.get_hackathon_by_id(hackathon_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    updates = payload.model_dump(exclude_unset=True)
    updated = db.update_hackathon(hackathon_id, updates)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update hackathon")
    return HackathonOut(**updated)

@router.delete("/{hackathon_id}")
async def delete_hackathon(
    hackathon_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete a hackathon.
    Only authorized admins can delete hackathons.
    """
    existing = db.get_hackathon_by_id(hackathon_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    success = db.delete_hackathon(hackathon_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete hackathon")
    return {"message": "Hackathon deleted successfully"}

