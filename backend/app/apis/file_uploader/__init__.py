from fastapi import APIRouter, File, UploadFile, HTTPException, Request, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import time
import mimetypes
from typing import Optional
import structlog
from sqlalchemy import func

# Import new services and database
from app.services.s3_service import s3_service
from app.services.email_service import email_service
from app.middleware.rate_limit import check_upload_rate_limit, record_upload
from app.database import get_db, Document

logger = structlog.get_logger()

router = APIRouter()

class FileUploadResponse(BaseModel):
    file_url: str
    file_path: str
    message: str
    document_id: int

class DocumentUploadRequest(BaseModel):
    title: str
    country: str
    state: str
    description: Optional[str] = None

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    country: str = Form(...),
    state: str = Form(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a document file to S3 and create a database entry.
    Rate limited to 1 upload per IP per 2 minutes.
    """
    
    # Check rate limit
    check_upload_rate_limit(request)
    
    try:
        # Validate file size (100MB limit)
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="File name is required"
            )
        
        # Anonymous upload - no IP tracking
        
        # Upload file to S3
        import io
        file_stream = io.BytesIO(file_content)
        
        file_path = s3_service.upload_file(
            file_stream,
            file.filename,
            file.content_type
        )
        
        if not file_path:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload file to storage"
            )
        
        # Get file URL
        file_url = s3_service.get_file_url(file_path)
        
        # Create database entry
        document = Document(
            title=title,
            country=country,
            state=state,
            description=description,
            file_path=file_path,
            file_url=file_url,
            original_filename=file.filename,
            file_size=len(file_content),
            content_type=file.content_type or "application/octet-stream",
            status="pending",  # Pending admin approval
            generated_tags=[]
        )
        
        try:
            db.add(document)
            db.commit()
            db.refresh(document)
            
            document_id = document.id
            
        except Exception as db_error:
            db.rollback()
            # If database insert fails, clean up the uploaded file
            s3_service.delete_file(file_path)
            logger.error("Database error during document creation", error=str(db_error))
            raise HTTPException(
                status_code=500,
                detail="Failed to create database entry"
            )
        
        # Send email notification to admin
        try:
            email_service.notify_admin_new_document(
                document_id=str(document_id),
                title=title,
                country=country,
                state=state,
                uploader_ip=None  # No IP tracking for privacy
            )
        except Exception as e:
            logger.warning("Failed to send email notification", error=str(e))
        
        # Record upload for rate limiting
        record_upload(request)
        
        logger.info("Document uploaded successfully", 
                   document_id=document_id,
                   file_path=file_path)
        
        return FileUploadResponse(
            file_url=file_url,
            file_path=file_path,
            document_id=document_id,
            message="File uploaded successfully. Document is pending admin approval and will be processed after approval."
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during file upload", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during file upload"
        )

@router.get("/rate-limit-status")
async def get_rate_limit_status(request: Request):
    """Get current rate limit status for the client."""
    from app.middleware.rate_limit import rate_limiter
    
    client_id = rate_limiter.get_client_identifier(request)
    remaining_time = rate_limiter.check_rate_limit(client_id, "upload")
    
    return {
        "rate_limited": remaining_time is not None,
        "remaining_time": int(remaining_time) if remaining_time else 0,
        "timeout_seconds": int(os.getenv("UPLOAD_TIMEOUT_SECONDS", "120"))
    }
