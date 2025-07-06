from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
import requests
import pytesseract
from pdf2image import convert_from_bytes
import spacy
import io
import re
import os
from collections import Counter
from typing import Optional, List
import structlog

# Import auth and database
from app.auth.user import AdminUser
from app.services.s3_service import s3_service
from app.services.email_service import email_service
from app.database import get_db, Document

logger = structlog.get_logger()

router = APIRouter()

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("spaCy model loaded successfully")
except OSError:
    logger.warning("spaCy model 'en_core_web_sm' not found. Tagging will be limited.")
    nlp = None 

class ProcessDocumentRequest(BaseModel):
    document_id: int
    pdf_url: str | None = None
    storage_key: str | None = None

class ProcessDocumentResponse(BaseModel):
    document_id: int
    ocr_text: str
    generated_tags: List[str]
    message: str

def clean_text(text: str) -> str:
    """Clean and normalize text from OCR."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep alphanumeric, spaces, and common punctuation
    text = re.sub(r'[^\w\s\-.,;:!?()[\]{}"]', '', text)
    return text.strip()

def extract_tags_from_text(text: str, max_tags: int = 50) -> List[str]:
    """Extract meaningful tags from text using spaCy NLP."""
    if not nlp or not text:
        return []
    
    try:
        # Process text with spaCy
        doc = nlp(text)
        
        # Extract entities (organizations, locations, etc.)
        entities = [ent.text.lower() for ent in doc.ents if len(ent.text) > 2]
        
        # Extract meaningful nouns and noun phrases
        nouns = []
        for token in doc:
            if token.pos_ in ['NOUN', 'PROPN'] and len(token.text) > 2:
                nouns.append(token.lemma_.lower())
        
        # Extract noun chunks
        noun_chunks = [chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text) > 2]
        
        # Combine all potential tags
        all_tags = entities + nouns + noun_chunks
        
        # Filter out common stop words and very short tags
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'these', 'those'}
        filtered_tags = [tag for tag in all_tags if tag not in stop_words and len(tag) > 2]
        
        # Count frequency and return most common
        tag_counts = Counter(filtered_tags)
        return [tag for tag, count in tag_counts.most_common(max_tags)]
        
    except Exception as e:
        logger.error("Error extracting tags from text", error=str(e))
        return []

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF using OCR."""
    try:
        # Convert PDF to images
        images = convert_from_bytes(pdf_content)
        
        # Extract text from each page
        extracted_text = []
        for image in images:
            # Use pytesseract to extract text
            text = pytesseract.image_to_string(image)
            extracted_text.append(text)
        
        # Combine all pages
        full_text = '\n'.join(extracted_text)
        return clean_text(full_text)
        
    except Exception as e:
        logger.error("Error extracting text from PDF", error=str(e))
        return ""

def extract_text_from_image(image_content: bytes) -> str:
    """Extract text from image using OCR."""
    try:
        # Use pytesseract to extract text directly from image bytes
        import PIL.Image
        image = PIL.Image.open(io.BytesIO(image_content))
        text = pytesseract.image_to_string(image)
        return clean_text(text)
        
    except Exception as e:
        logger.error("Error extracting text from image", error=str(e))
        return ""

@router.post("/process-document", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Process a document by extracting text using OCR and generating tags.
    Only admin users can process documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == request.document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get file content from S3
        file_path = document.file_path
        if not file_path:
            raise HTTPException(status_code=400, detail="Document file path not found")
        
        # Download file from S3
        file_url = s3_service.get_file_url(file_path)
        
        try:
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            file_content = response.content
        except requests.RequestException as e:
            logger.error("Failed to download file from S3", file_path=file_path, error=str(e))
            raise HTTPException(status_code=500, detail="Failed to download file from storage")
        
        # Extract text based on file type
        content_type = document.content_type.lower() if document.content_type else ""
        
        if "pdf" in content_type:
            extracted_text = extract_text_from_pdf(file_content)
        elif any(img_type in content_type for img_type in ["image", "jpeg", "jpg", "png", "gif", "bmp"]):
            extracted_text = extract_text_from_image(file_content)
        else:
            # For other document types, try to extract as text
            try:
                extracted_text = clean_text(file_content.decode('utf-8'))
            except UnicodeDecodeError:
                extracted_text = clean_text(file_content.decode('utf-8', errors='ignore'))
        
        if not extracted_text:
            logger.warning("No text extracted from document", document_id=request.document_id)
            extracted_text = ""
        
        # Generate tags from extracted text
        generated_tags = extract_tags_from_text(extracted_text)
        
        # Update document in database
        document.ocr_text = extracted_text
        document.generated_tags = generated_tags
        document.processed_at = func.now()
        document.status = "processed"
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during document update", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to update document")
        
        logger.info("Document processed successfully", 
                   document_id=request.document_id,
                   tags_count=len(generated_tags),
                   text_length=len(extracted_text))
        
        return ProcessDocumentResponse(
            document_id=request.document_id,
            ocr_text=extracted_text,
            generated_tags=generated_tags,
            message="Document processed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during document processing", 
                    document_id=request.document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during document processing"
        )

@router.post("/approve-document/{document_id}")
async def approve_document(
    document_id: int, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Approve a document for public display.
    Only admin users can approve documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update document status to approved
        document.status = "approved"
        document.approved_at = func.now()
        document.approved_by = admin_user.email
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during document approval", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to approve document")
        
        # Send notification email
        try:
            email_service.notify_admin_document_approved(
                document_id=str(document_id),
                title=document.title or "Unknown"
            )
        except Exception as e:
            logger.warning("Failed to send approval notification", error=str(e))
        
        logger.info("Document approved successfully", 
                   document_id=document_id,
                   approved_by=admin_user.email)
        
        return {"message": "Document approved successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during document approval", 
                    document_id=document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during document approval"
        )

@router.post("/reject-document/{document_id}")
async def reject_document(
    document_id: int, 
    admin_user: AdminUser,
    reason: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Reject a document.
    Only admin users can reject documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update document status to rejected
        document.status = "rejected"
        document.rejected_at = func.now()
        document.rejected_by = admin_user.email
        document.rejection_reason = reason
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during document rejection", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to reject document")
        
        # Send notification email
        try:
            email_service.notify_admin_document_rejected(
                document_id=str(document_id),
                title=document.title or "Unknown",
                reason=reason or ""
            )
        except Exception as e:
            logger.warning("Failed to send rejection notification", error=str(e))
        
        logger.info("Document rejected successfully", 
                   document_id=document_id,
                   rejected_by=admin_user.email,
                   reason=reason)
        
        return {"message": "Document rejected successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during document rejection", 
                    document_id=document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during document rejection"
        )
