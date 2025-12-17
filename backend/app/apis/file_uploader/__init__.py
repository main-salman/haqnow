from fastapi import APIRouter, File, UploadFile, HTTPException, Request, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import time
import mimetypes
from typing import Optional, List
import structlog
from sqlalchemy import func

# Import new services and database
from app.services.s3_service import s3_service
from app.services.email_service import email_service
from app.services.metadata_service import metadata_service
from app.services.virus_scanning_service import virus_scanning_service
from app.services.captcha_service import captcha_service
from app.services.queue_service import queue_service
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
    job_id: Optional[int] = None  # Job ID for tracking processing status

class MultiFileUploadResponse(BaseModel):
    """Response model for multiple file uploads"""
    uploaded_files: List[FileUploadResponse]
    total_count: int
    success_count: int
    failed_count: int
    message: str

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
    captcha_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    api_consumer: Optional[APIConsumer] = Depends(validate_api_key)
):
    """
    Upload a document file to S3 and create a database entry.
    Rate limited to 1 upload per IP per 2 minutes.
    Supports multiple languages including Arabic with Mistral API processing.
    """
    
    # Check rate limit only for anonymous or web clients.
    # If a valid API key is provided with 'upload' scope, skip rate limit and captcha.
    is_api_allowed = api_consumer is not None and (api_consumer.scopes and "upload" in api_consumer.scopes)
    if not is_api_allowed:
        check_upload_rate_limit(request)
        
        # Validate captcha token for web clients (only if secret key is configured)
        # If secret key is not configured, rely on frontend validation only (old behavior)
        if captcha_service.available:
            client_ip = request.client.host if request.client else None
            if not captcha_service.verify_token(captcha_token or "", client_ip):
                raise HTTPException(
                    status_code=400,
                    detail="Security verification failed. Please complete the captcha and try again."
                )
    
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
            message=message,
            job_id=None  # Job will be created when document is approved
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during file upload", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during file upload"
        )

@router.post("/upload-multiple", response_model=MultiFileUploadResponse)
async def upload_multiple_files(
    request: Request,
    files: List[UploadFile] = File(...),
    title: str = Form(...),
    country: str = Form(...),
    state: str = Form(...),
    document_language: str = Form(default="english"),
    description: Optional[str] = Form(None),
    captcha_token: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    api_consumer: Optional[APIConsumer] = Depends(validate_api_key)
):
    """
    Upload multiple document files to S3 and create database entries.
    Rate limited to 1 upload session per IP per 2 minutes.
    Supports multiple languages including Arabic with Mistral API processing.
    """
    
    # Check rate limit only for anonymous or web clients
    is_api_allowed = api_consumer is not None and (api_consumer.scopes and "upload" in api_consumer.scopes)
    if not is_api_allowed:
        check_upload_rate_limit(request)
        
        # Validate captcha token for web clients (only if secret key is configured)
        # If secret key is not configured, rely on frontend validation only (old behavior)
        if captcha_service.available:
            client_ip = request.client.host if request.client else None
            if not captcha_service.verify_token(captcha_token or "", client_ip):
                raise HTTPException(
                    status_code=400,
                    detail="Security verification failed. Please complete the captcha and try again."
                )
    
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 10:  # Limit to 10 files per upload
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")
    
    uploaded_results = []
    success_count = 0
    failed_count = 0
    
    for idx, file in enumerate(files):
        try:
            # Validate file size (100MB limit per file)
            MAX_FILE_SIZE = 100 * 1024 * 1024
            file_content = await file.read()
            
            if len(file_content) > MAX_FILE_SIZE:
                failed_count += 1
                logger.warning(f"File {file.filename} too large, skipping")
                continue
            
            if not file.filename:
                failed_count += 1
                continue
            
            # Validate document language
            valid_languages = ["english", "arabic", "french", "german", "spanish", "chinese", "russian", "other"]
            doc_language = document_language if document_language in valid_languages else "english"
            
            logger.info("Processing file in multi-upload", 
                       filename=file.filename,
                       file_index=idx + 1,
                       total_files=len(files))
            
            # Virus scan
            is_safe, virus_name = virus_scanning_service.scan_file_content(file_content, file.filename)
            if not is_safe:
                failed_count += 1
                logger.warning(f"Virus detected in {file.filename}, skipping")
                continue
            
            # Metadata stripping
            try:
                clean_pdf_bytes, clean_filename = metadata_service.process_uploaded_file(
                    file_content, 
                    file.filename, 
                    file.content_type or "application/octet-stream"
                )
            except Exception as e:
                failed_count += 1
                logger.error(f"Metadata stripping failed for {file.filename}", error=str(e))
                continue
            
            # Upload to S3
            import io
            clean_file_stream = io.BytesIO(clean_pdf_bytes)
            file_path = s3_service.upload_file(
                clean_file_stream,
                clean_filename,
                "application/pdf"
            )
            
            if not file_path:
                failed_count += 1
                continue
            
            file_url = s3_service.get_file_url(file_path)
            
            # Generate unique title for each file if multiple
            file_title = f"{title} - Part {idx + 1}" if len(files) > 1 else title
            
            # Create database entry
            document = Document(
                title=file_title,
                country=country,
                state=state,
                description=description,
                document_language=doc_language,
                file_path=file_path,
                file_url=file_url,
                original_filename=clean_filename,
                file_size=len(clean_pdf_bytes),
                content_type="application/pdf",
                status="pending",
                generated_tags=[]
            )
            
            try:
                db.add(document)
                db.commit()
                db.refresh(document)
                
                uploaded_results.append(FileUploadResponse(
                    file_url=file_url,
                    file_path=file_path,
                    document_id=document.id,
                    message=f"File {file.filename} uploaded successfully",
                    job_id=None
                ))
                success_count += 1
                
            except Exception as db_error:
                db.rollback()
                s3_service.delete_file(file_path)
                failed_count += 1
                logger.error(f"Database error for {file.filename}", error=str(db_error))
                continue
                
        except Exception as e:
            failed_count += 1
            logger.error(f"Error processing file {file.filename}", error=str(e))
            continue
    
    # Record upload for rate limiting
    if not is_api_allowed:
        record_upload(request)
    
    # Send single notification for batch upload
    if success_count > 0:
        try:
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
                document_id=f"Batch upload ({success_count} files)",
                title=title,
                country=country,
                state=state,
                uploader_ip=None,
                extra_recipients=recipients
            )
        except Exception as e:
            logger.warning("Failed to send batch email notification", error=str(e))
    
    return MultiFileUploadResponse(
        uploaded_files=uploaded_results,
        total_count=len(files),
        success_count=success_count,
        failed_count=failed_count,
        message=f"Uploaded {success_count} of {len(files)} files successfully"
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
