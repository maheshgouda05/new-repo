from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from backend.services.auth_service import require_admin, get_optional_user
from backend.database import db
from backend.models.event import AnnouncementCreate, AnnouncementUpdate, AnnouncementOut
from backend.services.storage_service import storage_service

router = APIRouter(prefix="/api/announcements", tags=["Announcements Management"])

@router.get("", response_model=List[AnnouncementOut])
async def list_announcements(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: Optional[dict] = Depends(get_optional_user)
):
    """
    List announcements.
    Public and members see only published notices.
    Admins can view drafts and all announcements.
    """
    is_admin = current_user and current_user.get("role") == "admin"
    if not is_admin:
        effective_status = status_filter if status_filter == "published" else "published"
    else:
        effective_status = status_filter

    announcements = db.list_announcements(status=effective_status)
    return [AnnouncementOut(**a) for a in announcements]

@router.post("", response_model=AnnouncementOut)
async def create_announcement(
    payload: AnnouncementCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Create a new announcement or notice.
    Only authorized admins can publish announcements.
    """
    a_dict = payload.model_dump()
    created = db.create_announcement(a_dict, created_by=current_user["id"])
    return AnnouncementOut(**created)

@router.post("/upload-image")
async def upload_announcement_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin)
):
    """
    Upload an announcement poster or photo to Supabase Storage.
    """
    url = await storage_service.upload_file(file, bucket="posters")
    return {"url": url}

@router.put("/{announcement_id}", response_model=AnnouncementOut)
async def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Update an announcement.
    Only authorized admins can edit announcements.
    """
    updates = payload.model_dump(exclude_unset=True)
    updated = db.update_announcement(announcement_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return AnnouncementOut(**updated)

@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    current_user: dict = Depends(require_admin)
):
    """
    Delete an announcement.
    Only authorized admins can delete announcements.
    """
    success = db.delete_announcement(announcement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement deleted successfully"}

