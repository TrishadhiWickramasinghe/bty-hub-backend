from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from config.database import get_database
from config.settings import settings
from middleware import get_current_admin
import aiofiles
import os
from pathlib import Path
from uuid import uuid4

router = APIRouter(prefix="/upload", tags=["Upload"])


async def save_upload_file(upload_file: UploadFile, subfolder: str = "products") -> str:
    """Save uploaded file and return the file path"""
    # Create upload directory if not exists
    upload_dir = Path(settings.UPLOAD_DIR) / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await upload_file.read()
        
        # Check file size
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        await out_file.write(content)
    
    # Return relative path
    return f"/{subfolder}/{unique_filename}"


@router.post("/product-image")
async def upload_product_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_admin)
):
    """Upload product image (Admin only)"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed"
        )
    
    try:
        file_path = await save_upload_file(file, "products")
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "url": f"{settings.API_V1_PREFIX}/static{file_path}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/category-image")
async def upload_category_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_admin)
):
    """Upload category image (Admin only)"""
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and WebP images are allowed"
        )
    
    try:
        file_path = await save_upload_file(file, "categories")
        return {
            "message": "File uploaded successfully",
            "file_path": file_path,
            "url": f"{settings.API_V1_PREFIX}/static{file_path}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
