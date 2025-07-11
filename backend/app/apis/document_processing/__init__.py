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
from app.database import get_db, Document, BannedTag

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

class DocumentListResponse(BaseModel):
    documents: List[dict]
    total_count: int
    page: int
    per_page: int

def clean_text(text: str) -> str:
    """Clean and normalize text from OCR."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep alphanumeric, spaces, and common punctuation
    text = re.sub(r'[^\w\s\-.,;:!?()[\]{}"]', '', text)
    return text.strip()

def filter_banned_words(text: str, banned_words: List[str]) -> str:
    """Filter banned words from text content."""
    if not text or not banned_words:
        return text
    
    try:
        # Create a case-insensitive replacement pattern
        for banned_word in banned_words:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(banned_word.lower()) + r'\b'
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        
        return text
    except Exception as e:
        logger.error("Error filtering banned words", error=str(e))
        return text

def get_banned_words(db: Session) -> List[str]:
    """Get list of banned words from database."""
    try:
        banned_tags = db.query(BannedTag).all()
        return [tag.tag.lower() for tag in banned_tags]
    except Exception as e:
        logger.error("Error retrieving banned words", error=str(e))
        return []

def get_top_words_for_search(text: str, max_words: int = 1000) -> str:
    """
    Extract the top most important words from text for search purposes.
    Uses word frequency and importance scoring.
    """
    if not text:
        return ""
    
    try:
        # Clean and split text into words
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        
        if len(words) <= max_words:
            return text
        
        # Define stop words to exclude from top words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'a', 'an', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'it', 'he', 'she',
            'they', 'we', 'you', 'i', 'me', 'him', 'her', 'them', 'us', 'my', 'your',
            'his', 'her', 'its', 'our', 'their', 'who', 'what', 'where', 'when', 'why',
            'how', 'which', 'than', 'so', 'very', 'just', 'now', 'then', 'here', 'there'
        }
        
        # Count word frequencies, excluding stop words
        word_counts = Counter()
        for word in words:
            if word not in stop_words and len(word) >= 3:
                word_counts[word] += 1
        
        # Get top words by frequency
        top_words = [word for word, count in word_counts.most_common(max_words)]
        
        # Reconstruct text using only top words
        result_words = []
        word_set = set(top_words)
        
        for word in words:
            if word in word_set:
                result_words.append(word)
            if len(result_words) >= max_words:
                break
        
        return ' '.join(result_words)
        
    except Exception as e:
        logger.error("Error extracting top words for search", error=str(e))
        # Fallback to first 1000 words if processing fails
        words = text.split()
        return ' '.join(words[:max_words]) if len(words) > max_words else text

def extract_tags_from_text(text: str, max_tags: int = 50, db: Session = None) -> List[str]:
    """Extract meaningful tags from text using spaCy NLP, filtering out banned words."""
    if not nlp or not text:
        return []
    
    try:
        # Get banned words if database session is available
        banned_words = []
        if db:
            banned_words = get_banned_words(db)
        
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
        
        # Filter out common stop words, very short tags, and banned words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'this', 'that', 'these', 'those'}
        filtered_tags = []
        for tag in all_tags:
            if (tag not in stop_words and 
                len(tag) > 2 and 
                tag.lower() not in banned_words):
                filtered_tags.append(tag)
        
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

def extract_text_from_docx(docx_content: bytes) -> str:
    """Extract text from Word document (.docx)."""
    try:
        from docx import Document as DocxDocument
        document = DocxDocument(io.BytesIO(docx_content))
        
        text_parts = []
        for paragraph in document.paragraphs:
            text_parts.append(paragraph.text)
        
        full_text = '\n'.join(text_parts)
        return clean_text(full_text)
        
    except Exception as e:
        logger.error("Error extracting text from DOCX", error=str(e))
        return ""

def extract_text_from_csv(csv_content: bytes) -> str:
    """Extract text from CSV file."""
    try:
        import csv
        text_content = csv_content.decode('utf-8', errors='ignore')
        csv_reader = csv.reader(io.StringIO(text_content))
        
        text_parts = []
        for row in csv_reader:
            text_parts.append(' '.join(row))
        
        full_text = '\n'.join(text_parts)
        return clean_text(full_text)
        
    except Exception as e:
        logger.error("Error extracting text from CSV", error=str(e))
        return ""

def extract_text_from_excel(excel_content: bytes) -> str:
    """Extract text from Excel file (.xls/.xlsx)."""
    try:
        import pandas as pd
        
        # Try to read the Excel file
        df = pd.read_excel(io.BytesIO(excel_content), sheet_name=None)  # Read all sheets
        
        text_parts = []
        for sheet_name, sheet_df in df.items():
            text_parts.append(f"Sheet: {sheet_name}")
            # Convert all values to string and join
            for column in sheet_df.columns:
                text_parts.extend(sheet_df[column].astype(str).tolist())
        
        full_text = '\n'.join(text_parts)
        return clean_text(full_text)
        
    except Exception as e:
        logger.error("Error extracting text from Excel", error=str(e))
        return ""

def extract_text_from_document(file_content: bytes, content_type: str) -> str:
    """Extract text from various document types."""
    content_type = content_type.lower() if content_type else ""
    
    # PDF files
    if "pdf" in content_type:
        return extract_text_from_pdf(file_content)
    
    # Image files  
    elif any(img_type in content_type for img_type in ["image", "jpeg", "jpg", "png", "gif", "bmp", "tiff", "webp"]):
        return extract_text_from_image(file_content)
    
    # Word documents
    elif "wordprocessingml" in content_type or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_content)
    
    # Excel files
    elif "spreadsheetml" in content_type or content_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        return extract_text_from_excel(file_content)
    
    # CSV files
    elif "csv" in content_type or content_type == "text/csv":
        return extract_text_from_csv(file_content)
    
    # Plain text files
    elif "text" in content_type:
        try:
            return clean_text(file_content.decode('utf-8'))
        except UnicodeDecodeError:
            return clean_text(file_content.decode('utf-8', errors='ignore'))
    
    # RTF files
    elif "rtf" in content_type:
        try:
            # Basic RTF handling - strip RTF codes
            text_content = file_content.decode('utf-8', errors='ignore')
            # Remove RTF control codes (basic cleanup)
            import re
            text_content = re.sub(r'\\[a-z]+\d*', '', text_content)
            text_content = re.sub(r'[{}]', '', text_content)
            return clean_text(text_content)
        except Exception as e:
            logger.error("Error extracting text from RTF", error=str(e))
            return ""
    
    # Default: try to decode as text
    else:
        try:
            return clean_text(file_content.decode('utf-8'))
        except UnicodeDecodeError:
            try:
                return clean_text(file_content.decode('latin-1', errors='ignore'))
            except Exception:
                logger.warning("Could not extract text from unknown file type", content_type=content_type)
                return ""

async def process_document_internal(document_id: int, db: Session) -> dict | None:
    """
    Internal function to process a document without requiring admin authentication.
    Used for automatic processing after upload.
    Returns processing result dict or None if failed.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error("Document not found for internal processing", document_id=document_id)
            return None
        
        # Get file content from S3
        file_path = document.file_path
        if not file_path:
            logger.error("Document file path not found", document_id=document_id)
            return None
        
        # Download file from S3
        file_url = s3_service.get_file_url(file_path)
        
        try:
            response = requests.get(file_url, timeout=30)
            response.raise_for_status()
            file_content = response.content
        except requests.RequestException as e:
            logger.error("Failed to download file from S3 for internal processing", 
                        file_path=file_path, error=str(e))
            return None
        
        # Extract text based on file type
        content_type = document.content_type.lower() if document.content_type else ""
        
        extracted_text = extract_text_from_document(file_content, content_type)
        
        if not extracted_text:
            logger.warning("No text extracted from document during internal processing", document_id=document_id)
            extracted_text = ""
        
        # Filter banned words from full OCR text first
        banned_words = get_banned_words(db)
        if banned_words:
            extracted_text = filter_banned_words(extracted_text, banned_words)
            logger.info("Banned words filtered from OCR text",
                       document_id=document_id,
                       banned_words_count=len(banned_words))
        
        # Get top 1000 most important words for database storage and search
        searchable_text = get_top_words_for_search(extracted_text, max_words=1000)
        original_word_count = len(extracted_text.split()) if extracted_text else 0
        searchable_word_count = len(searchable_text.split()) if searchable_text else 0
        
        logger.info("OCR text processed for search", 
                   document_id=document_id,
                   original_words=original_word_count,
                   searchable_words=searchable_word_count)
        
        # Generate tags from extracted text
        generated_tags = extract_tags_from_text(extracted_text, db=db)
        
        # Update document in database with searchable text (top 1000 words)
        document.ocr_text = searchable_text
        document.generated_tags = generated_tags
        document.processed_at = func.now()
        document.status = "processed"
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during internal document processing", error=str(db_error))
            return None
        
        logger.info("Document processed internally", 
                   document_id=document_id,
                   tags_count=len(generated_tags),
                   text_length=len(searchable_text))
        
        return {
            "document_id": document_id,
            "ocr_text": searchable_text,
            "generated_tags": generated_tags,
            "status": "processed"
        }
        
    except Exception as e:
        logger.error("Unexpected error during internal document processing", 
                    document_id=document_id,
                    error=str(e))
        return None

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
        
        extracted_text = extract_text_from_document(file_content, content_type)
        
        if not extracted_text:
            logger.warning("No text extracted from document", document_id=request.document_id)
            extracted_text = ""
        
        # Filter banned words from full OCR text first
        banned_words = get_banned_words(db)
        if banned_words:
            extracted_text = filter_banned_words(extracted_text, banned_words)
            logger.info("Banned words filtered from OCR text",
                       document_id=request.document_id,
                       banned_words_count=len(banned_words))
        
        # Get top 1000 most important words for database storage and search
        searchable_text = get_top_words_for_search(extracted_text, max_words=1000)
        original_word_count = len(extracted_text.split()) if extracted_text else 0
        searchable_word_count = len(searchable_text.split()) if searchable_text else 0
        
        logger.info("OCR text processed for search", 
                   document_id=request.document_id,
                   original_words=original_word_count,
                   searchable_words=searchable_word_count)
        
        # Generate tags from extracted text
        generated_tags = extract_tags_from_text(extracted_text, db=db)
        
        # Update document in database with searchable text (top 1000 words)
        document.ocr_text = searchable_text
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
                   text_length=len(searchable_text))
        
        return ProcessDocumentResponse(
            document_id=request.document_id,
            ocr_text=searchable_text,
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
    Approve a document for public display and trigger OCR processing.
    Only admin users can approve documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document is in pending status
        if document.status != "pending":
            raise HTTPException(status_code=400, detail=f"Document is not pending approval (current status: {document.status})")
        
        # Process the document first (OCR + tagging)
        processing_result = await process_document_internal(document_id, db)
        
        if not processing_result:
            raise HTTPException(status_code=500, detail="Failed to process document during approval")
        
        # Update document status to approved after successful processing
        document = db.query(Document).filter(Document.id == document_id).first()  # Refresh from DB
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
        
        logger.info("Document approved and processed successfully", 
                   document_id=document_id,
                   approved_by=admin_user.email,
                   tags_count=len(processing_result.get('generated_tags', [])),
                   text_length=len(processing_result.get('ocr_text', '')))
        
        return {
            "message": "Document approved and processed successfully", 
            "document_id": document_id,
            "ocr_text_length": len(processing_result.get('ocr_text', '')),
            "tags_generated": len(processing_result.get('generated_tags', []))
        }
        
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

@router.delete("/delete-document/{document_id}")
async def delete_document(
    document_id: int, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Permanently delete a document and its associated file.
    Only admin users can delete documents.
    """
    
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Store document info for logging
        document_title = document.title
        file_path = document.file_path
        
        # Delete file from S3 if it exists
        if file_path:
            try:
                s3_service.delete_file(file_path)
                logger.info("File deleted from S3", file_path=file_path)
            except Exception as e:
                logger.warning("Failed to delete file from S3", file_path=file_path, error=str(e))
                # Continue with database deletion even if S3 deletion fails
        
        # Delete document from database
        try:
            db.delete(document)
            db.commit()
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during document deletion", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to delete document from database")
        
        logger.info("Document deleted successfully", 
                   document_id=document_id,
                   title=document_title,
                   deleted_by=admin_user.email)
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error during document deletion", 
                    document_id=document_id,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during document deletion"
        )

@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    admin_user: AdminUser,
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected, processed"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db)
):
    """
    Get documents with optional status filter.
    Only admin users can access this endpoint.
    """
    
    try:
        # Build query
        query_builder = db.query(Document)
        
        # Filter by status if provided
        if status:
            query_builder = query_builder.filter(Document.status == status)
        
        # Get total count before pagination
        total_count = query_builder.count()
        
        # Order by created_at descending
        query_builder = query_builder.order_by(Document.created_at.desc())
        
        # Apply pagination
        offset = (page - 1) * per_page
        query_builder = query_builder.offset(offset).limit(per_page)
        
        # Execute query
        documents_data = query_builder.all()
        
        # Convert to response format
        documents = []
        for doc in documents_data:
            documents.append({
                "id": doc.id,
                "title": doc.title,
                "country": doc.country,
                "state": doc.state,
                "description": doc.description,
                "file_path": doc.file_path,
                "file_url": doc.file_url,
                "original_filename": doc.original_filename,
                "file_size": doc.file_size,
                "content_type": doc.content_type,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                "approved_at": doc.approved_at.isoformat() if doc.approved_at else None,
                "rejected_at": doc.rejected_at.isoformat() if doc.rejected_at else None,
                "approved_by": doc.approved_by,
                "rejected_by": doc.rejected_by,
                "rejection_reason": doc.rejection_reason,
                "ocr_text": doc.ocr_text,
                "generated_tags": doc.generated_tags
            })
        
        logger.info("Documents retrieved successfully", 
                   status=status,
                   results_count=len(documents),
                   page=page)
        
        return DocumentListResponse(
            documents=documents,
            total_count=total_count,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error("Error retrieving documents", status=status, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving documents"
        )

@router.get("/document/{document_id}")
async def get_document_by_id(
    document_id: int, 
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID for admin purposes.
    Only admin users can access this endpoint.
    """
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Convert to response format
        document_data = {
            "id": document.id,
            "title": document.title,
            "country": document.country,
            "state": document.state,
            "description": document.description,
            "file_path": document.file_path,
            "file_url": document.file_url,
            "original_filename": document.original_filename,
            "file_size": document.file_size,
            "content_type": document.content_type,
            "status": document.status,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "approved_at": document.approved_at.isoformat() if document.approved_at else None,
            "rejected_at": document.rejected_at.isoformat() if document.rejected_at else None,
            "approved_by": document.approved_by,
            "rejected_by": document.rejected_by,
            "rejection_reason": document.rejection_reason,
            "ocr_text": document.ocr_text,
            "generated_tags": document.generated_tags
        }
        
        logger.info("Document retrieved successfully", document_id=document_id)
        
        return document_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving the document"
        )
