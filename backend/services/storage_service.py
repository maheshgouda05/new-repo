import uuid
import os
import shutil
from pathlib import Path
from fastapi import UploadFile, HTTPException
from backend.config import settings
from backend.database import supabase_client

class StorageService:
    @staticmethod
    async def upload_file(file: UploadFile, bucket: str = "posters") -> str:
        """
        Uploads a file to Supabase Storage if configured;
        Otherwise saves it locally into frontend/assets/uploads/ and serves it statically.
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
            
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file format. Only JPG, PNG, WEBP, and GIF images are allowed."
            )
            
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        contents = await file.read()

        # 1. Try Supabase Storage if configured
        if supabase_client and settings.is_supabase_configured:
            try:
                # Upload to Supabase bucket
                res = supabase_client.storage.from_(bucket).upload(
                    path=unique_filename,
                    file=contents,
                    file_options={"content-type": file.content_type}
                )
                # Retrieve public URL
                public_url = supabase_client.storage.from_(bucket).get_public_url(unique_filename)
                return public_url
            except Exception as e:
                # Fall back to local file storage if Supabase upload fails
                pass

        # 2. Local fallback storage
        local_target = settings.UPLOAD_DIR / unique_filename
        with open(local_target, "wb") as f:
            f.write(contents)

        return f"/assets/uploads/{unique_filename}"

storage_service = StorageService()

