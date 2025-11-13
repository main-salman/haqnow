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
from app.services.metadata_service import metadata_service
from app.services.virus_scanning_service import virus_scanning_service
from app.database import SiteSetting
import json

# Optional RAG service import
try:
    from app.services.rag_service import rag_service
    RAG_AVAILABLE = True
except ImportError:
    rag_service = None
    RAG_AVAILABLE = False
from app.middleware.rate_limit import check_upload_rate_limit, record_upload
from app.database import get_db, Document
from app.auth.jwt_auth import validate_api_key, APIConsumer

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
    document_language: str = Form(default="english"),  # Added document language parameter
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    api_consumer: Optional[APIConsumer] = Depends(validate_api_key)
):
    """
    Upload a document file to S3 and create a database entry.
    Rate limited to 1 upload per IP per 2 minutes.
    Supports multiple languages including Arabic with Mistral API processing.
    """
    
    # Check rate limit only for anonymous or web clients.
    # If a valid API key is provided with 'upload' scope, skip rate limit.
    is_api_allowed = api_consumer is not None and (api_consumer.scopes and "upload" in api_consumer.scopes)
    if not is_api_allowed:
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
        
        # Validate document language
        valid_languages = ["english", "arabic", "french", "german", "spanish", "chinese", "russian", "other"]
        if document_language not in valid_languages:
            document_language = "english"  # Default fallback
            
        logger.info("Document upload started", 
                   filename=file.filename,
                   language=document_language,
                   country=country)
        
        # Anonymous upload - no IP tracking
        
        # VIRUS SCANNING: Scan file for viruses/malware before processing
        logger.info("Starting virus scan", filename=file.filename)
        is_safe, virus_name = virus_scanning_service.scan_file_content(file_content, file.filename)
        
        if not is_safe:
            logger.error(
                "Virus detected in uploaded file - upload rejected",
                filename=file.filename,
                virus=virus_name
            )
            raise HTTPException(
                status_code=400,
                detail=f"File upload rejected: {virus_name or 'Virus or malware detected'}. Your file has been deleted for security reasons."
            )
        
        logger.info("Virus scan completed - file is clean", filename=file.filename)
        
        # PRIVACY PROTECTION: Strip metadata and convert to clean PDF
        logger.info("Starting metadata stripping process",
                   original_filename=file.filename,
                   original_size=len(file_content))
        
        try:
            clean_pdf_bytes, clean_filename = metadata_service.process_uploaded_file(
                file_content, 
                file.filename, 
                file.content_type or "application/octet-stream"
            )
            
            logger.info("Metadata stripping completed",
                       original_filename=file.filename,
                       clean_filename=clean_filename,
                       original_size=len(file_content),
                       clean_size=len(clean_pdf_bytes))
        
        except Exception as e:
            logger.error("Metadata stripping failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail="Failed to process file for privacy protection"
            )
        
        # Upload ONLY the clean PDF to S3 (original file is never stored)
        import io
        clean_file_stream = io.BytesIO(clean_pdf_bytes)
        
        file_path = s3_service.upload_file(
            clean_file_stream,
            clean_filename,
            "application/pdf"  # All files are now PDFs
        )
        
        if not file_path:
            raise HTTPException(
                status_code=500,
                detail="Failed to upload cleaned file to storage"
            )
        
        # Get file URL
        file_url = s3_service.get_file_url(file_path)
        
        # Create database entry (storing clean PDF information only)
        document = Document(
            title=title,
            country=country,
            state=state,
            description=description,
            document_language=document_language,  # Store document language
            file_path=file_path,
            file_url=file_url,
            original_filename=clean_filename,  # Store clean filename
            file_size=len(clean_pdf_bytes),    # Store clean file size
            content_type="application/pdf",    # All files are now PDFs
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
        
        # Send email notification to configured recipients
        try:
            # Fetch configured notification recipients from site settings
            recipients: list[str] = []
            try:
                setting = db.query(SiteSetting).filter(SiteSetting.key == "upload_notification_emails").first()
                if setting and setting.value:
                    data = json.loads(setting.value)
                    emails = data.get("emails") if isinstance(data, dict) else data
                    if isinstance(emails, list):
                        recipients = [e.strip() for e in emails if isinstance(e, str) and e and e.strip()]
            except Exception:
                recipients = []

            email_service.notify_admin_new_document(
                document_id=str(document_id),
                title=title,
                country=country,
                state=state,
                uploader_ip=None,
                extra_recipients=recipients
            )
        except Exception as e:
            logger.warning("Failed to send email notification", error=str(e))
        
        # Record upload for rate limiting when anonymous/web client
        if not is_api_allowed:
            record_upload(request)
        
        logger.info("Document uploaded successfully", 
                   document_id=document_id,
                   language=document_language,
                   file_path=file_path)
        
        # Success message varies based on language
        if document_language == "arabic":
            message = "File uploaded successfully with complete metadata removal for privacy protection. Arabic document will be processed with OCR and translation when approved by admin."
        else:
            message = "File uploaded successfully with complete metadata removal for privacy protection. Document converted to clean PDF format and is pending admin approval."
        
        return FileUploadResponse(
            file_url=file_url,
            file_path=file_path,
            document_id=document_id,
            message=message
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
