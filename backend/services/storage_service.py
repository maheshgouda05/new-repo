import uuid
import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from backend.config import settings
from backend.database import supabase_client

logger = logging.getLogger("analytix.storage")

ALLOWED_MIME_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "image/gif": [".gif"]
}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

def validate_image_bytes(contents: bytes) -> bool:
    """Validates real image header magic bytes against spoofed file extensions."""
    if len(contents) < 12:
        return False
    # JPEG: starts with \xff\xd8\xff
    if contents.startswith(b"\xff\xd8\xff"):
        return True
    # PNG: starts with \x89PNG\r\n\x1a\n
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # GIF: starts with GIF87a or GIF89a
    if contents.startswith(b"GIF87a") or contents.startswith(b"GIF89a"):
        return True
    # WEBP: starts with RIFF and bytes 8..12 are WEBP
    if contents.startswith(b"RIFF") and contents[8:12] == b"WEBP":
        return True
    return False

class StorageService:
    @staticmethod
    async def upload_file(file: UploadFile, bucket: str = "posters") -> str:
        """
        Uploads an image file to Supabase Storage with strict MIME, magic byte,
        and size validations.
        In production, Supabase Storage is mandatory (no ephemeral local disk fallback).
        """
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="No file selected for upload."
            )
            
        file_ext = Path(file.filename).suffix.lower()
        content_type = (file.content_type or "").lower().split(";")[0].strip()

        # 1. Validate file extension and MIME type
        is_valid_ext = any(file_ext in exts for exts in ALLOWED_MIME_TYPES.values())
        is_valid_mime = content_type in ALLOWED_MIME_TYPES or content_type == "application/octet-stream"
        if not (is_valid_ext and is_valid_mime):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Invalid image file type ({file_ext}). Only JPG, PNG, WEBP, and GIF images are allowed."
            )
            
        contents = await file.read()
        
        # 2. Validate maximum file size (5MB)
        if len(contents) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of 5 MB (current size: {len(contents) / (1024*1024):.1f} MB)."
            )

        # 3. Validate binary magic bytes
        if not validate_image_bytes(contents):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match a valid image format. Corrupted or disguised file rejected."
            )

        unique_filename = f"{uuid.uuid4().hex}{file_ext}"

        # 4. Mandatory Cloud Storage in Production
        if settings.ENVIRONMENT == "production":
            if not (supabase_client and settings.is_supabase_configured):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Cloud storage service is unconfigured. Local fallback is disabled in production."
                )
            try:
                final_content_type = content_type if content_type in ALLOWED_MIME_TYPES else "image/jpeg"
                supabase_client.storage.from_(bucket).upload(
                    path=unique_filename,
                    file=contents,
                    file_options={"content-type": final_content_type, "upsert": "true"}
                )
                public_url = supabase_client.storage.from_(bucket).get_public_url(unique_filename)
                logger.info(f"Uploaded image to Supabase bucket '{bucket}': {public_url}")
                return public_url
            except Exception as e:
                logger.error(f"Supabase Storage upload failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Cloud storage upload error: {str(e)}"
                )

        # 5. Non-production / local development
        if supabase_client and settings.is_supabase_configured:
            try:
                final_content_type = content_type if content_type in ALLOWED_MIME_TYPES else "image/jpeg"
                supabase_client.storage.from_(bucket).upload(
                    path=unique_filename,
                    file=contents,
                    file_options={"content-type": final_content_type, "upsert": "true"}
                )
                return supabase_client.storage.from_(bucket).get_public_url(unique_filename)
            except Exception as e:
                logger.warning(f"Development fallback: Supabase storage failed ({e}), writing locally.")

        local_target = settings.UPLOAD_DIR / unique_filename
        with open(local_target, "wb") as f:
            f.write(contents)

        return f"/assets/uploads/{unique_filename}"

storage_service = StorageService()
