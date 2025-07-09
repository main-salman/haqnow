import json
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
import os
import structlog

# Import rate limiting, auth, and database
from app.middleware.rate_limit import check_download_rate_limit, record_download
from app.auth.user import AdminUser
from app.database import get_db, Document, BannedTag

logger = structlog.get_logger()

router = APIRouter()

# --- Pydantic Models ---
class SearchDocumentResult(BaseModel):
    id: int
    title: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    generated_tags: Optional[List[str]] = None
    ocr_text: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None

class SearchResponse(BaseModel):
    documents: List[SearchDocumentResult]
    total_count: int
    page: int
    per_page: int
    grouped_by_country: Optional[dict] = None

class AddTagRequest(BaseModel):
    document_id: int
    tag: str

class AddTagResponse(BaseModel):
    message: str
    document_id: int
    tag: str

@router.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    country: Optional[str] = Query(None, description="Filter by country"),
    state: Optional[str] = Query(None, description="Filter by state"),
    group_by_country: bool = Query(False, description="Group results by country"),
    db: Session = Depends(get_db)
):
    """
    Search documents by text content and tags.
    Returns only approved documents.
    """
    
    try:
        # Build query
        query_builder = db.query(Document)
        
        # Filter by status (only approved documents)
        query_builder = query_builder.filter(Document.status == "approved")
        
        # Search in title, description, OCR text, and tags
        if q:
            # Create search conditions for different fields
            search_conditions = []
            
            # Search in title and description
            search_conditions.append(Document.title.ilike(f"%{q}%"))
            search_conditions.append(Document.description.ilike(f"%{q}%"))
            search_conditions.append(Document.ocr_text.ilike(f"%{q}%"))
            
            # Search in generated_tags (JSON field)
            # For MySQL JSON search, we need to use JSON functions
            search_conditions.append(func.json_search(Document.generated_tags, 'one', f"%{q}%").isnot(None))
            
            # Apply OR condition for all search fields
            query_builder = query_builder.filter(or_(*search_conditions))
        
        # Filter by country
        if country:
            query_builder = query_builder.filter(Document.country == country)
        
        # Filter by state
        if state:
            query_builder = query_builder.filter(Document.state == state)
        
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
            doc_dict = doc.to_dict()
            documents.append(SearchDocumentResult(**doc_dict))
        
        # Group by country if requested
        grouped_by_country = None
        if group_by_country and documents:
            grouped_by_country = {}
            for doc in documents:
                if doc.country:
                    if doc.country not in grouped_by_country:
                        grouped_by_country[doc.country] = []
                    grouped_by_country[doc.country].append(doc)
        
        logger.info("Search completed successfully", 
                   query=q,
                   results_count=len(documents),
                   page=page)
        
        return SearchResponse(
            documents=documents,
            total_count=total_count,
            page=page,
            per_page=per_page,
            grouped_by_country=grouped_by_country
        )
        
    except Exception as e:
        logger.error("Error during search", query=q, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred during search"
        )

@router.get("/document/{document_id}", response_model=SearchDocumentResult)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    Get a specific document by ID.
    Returns only approved documents.
    """
    
    try:
        document = db.query(Document).filter(
            and_(Document.id == document_id, Document.status == "approved")
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info("Document retrieved successfully", document_id=document_id)
        
        doc_dict = document.to_dict()
        return SearchDocumentResult(**doc_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving the document"
        )

@router.get("/download/{document_id}")
async def download_document(
    document_id: int, 
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get download URL for a document.
    Rate limited to prevent abuse.
    """
    
    # Check rate limit
    check_download_rate_limit(request)
    
    try:
        # Get document from database
        document = db.query(Document).filter(
            and_(Document.id == document_id, Document.status == "approved")
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = document.file_path
        
        if not file_path:
            raise HTTPException(status_code=400, detail="Document file not available")
        
        # Get S3 service
        from app.services.s3_service import s3_service
        
        # Generate download URL
        download_url = s3_service.get_download_url(file_path)
        
        if not download_url:
            raise HTTPException(status_code=500, detail="Failed to generate download URL")
        
        # Record download for rate limiting
        record_download(request)
        
        logger.info("Download URL generated successfully", 
                   document_id=document_id,
                   client_ip=request.client.host if request.client else "unknown")
        
        return {"download_url": download_url, "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating download URL", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating download URL"
        )

@router.post("/add-tag", response_model=AddTagResponse)
async def add_tag(request: AddTagRequest, db: Session = Depends(get_db)):
    """
    Add a tag to a document.
    Limited to 1000 tags per document.
    """
    
    try:
        # Check if tag is banned
        banned_tag = db.query(BannedTag).filter(BannedTag.tag == request.tag.lower()).first()
        if banned_tag:
            raise HTTPException(status_code=400, detail="This tag has been banned by administrators")
        
        # Get document from database
        document = db.query(Document).filter(
            and_(Document.id == request.document_id, Document.status == "approved")
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        current_tags = document.generated_tags or []
        
        # Check if tag already exists (case insensitive)
        if request.tag.lower() in [tag.lower() for tag in current_tags]:
            raise HTTPException(status_code=400, detail="Tag already exists")
        
        # Check tag limit
        if len(current_tags) >= 1000:
            raise HTTPException(status_code=400, detail="Maximum number of tags (1000) reached")
        
        # Validate tag (basic validation)
        if not request.tag.strip() or len(request.tag.strip()) < 2:
            raise HTTPException(status_code=400, detail="Tag must be at least 2 characters long")
        
        if len(request.tag.strip()) > 50:
            raise HTTPException(status_code=400, detail="Tag must be no more than 50 characters long")
        
        # Add tag to list
        new_tags = current_tags + [request.tag.strip()]
        document.generated_tags = new_tags
        
        try:
            db.commit()
            db.refresh(document)
        except Exception as db_error:
            db.rollback()
            logger.error("Database error during tag addition", error=str(db_error))
            raise HTTPException(status_code=500, detail="Failed to add tag")
        
        logger.info("Tag added successfully", 
                   document_id=request.document_id,
                   tag=request.tag)
        
        return AddTagResponse(
            message="Tag added successfully",
            document_id=request.document_id,
            tag=request.tag
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error adding tag", document_id=request.document_id, tag=request.tag, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while adding the tag"
        )

@router.get("/tags/{document_id}")
async def get_document_tags(document_id: int, db: Session = Depends(get_db)):
    """Get all tags for a document."""
    
    try:
        document = db.query(Document).filter(
            and_(Document.id == document_id, Document.status == "approved")
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        tags = document.generated_tags or []
        
        return {"document_id": document_id, "tags": tags, "count": len(tags)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving tags", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving tags"
        )

@router.get("/banned-tags")
async def get_banned_tags(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Get all banned tags (admin only)."""
    
    try:
        banned_tags = db.query(BannedTag).order_by(BannedTag.banned_at.desc()).all()
        
        tags_list = []
        for banned_tag in banned_tags:
            tags_list.append({
                "id": banned_tag.id,
                "tag": banned_tag.tag,
                "reason": banned_tag.reason,
                "banned_by": banned_tag.banned_by,
                "banned_at": banned_tag.banned_at.isoformat() if banned_tag.banned_at else None
            })
        
        logger.info("Banned tags retrieved successfully", count=len(tags_list))
        
        return {"banned_tags": tags_list, "count": len(tags_list)}
        
    except Exception as e:
        logger.error("Error retrieving banned tags", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving banned tags"
        )

@router.post("/ban-tag")
async def ban_tag(
    tag: str,
    admin_user: AdminUser,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Ban a tag (admin only)."""
    
    try:
        # Check if tag is already banned
        existing_ban = db.query(BannedTag).filter(BannedTag.tag == tag.lower()).first()
        if existing_ban:
            raise HTTPException(status_code=400, detail="Tag is already banned")
        
        # Create banned tag entry
        banned_tag = BannedTag(
            tag=tag.lower(),
            reason=reason,
            banned_by=admin_user.email
        )
        
        db.add(banned_tag)
        db.commit()
        db.refresh(banned_tag)
        
        logger.info("Tag banned successfully", tag=tag, banned_by=admin_user.email)
        
        return {"message": "Tag banned successfully", "tag": tag}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error banning tag", tag=tag, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while banning the tag"
        )

@router.delete("/unban-tag/{tag_id}")
async def unban_tag(
    tag_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Unban a tag by ID (admin only)."""
    
    try:
        # Get banned tag by ID
        banned_tag = db.query(BannedTag).filter(BannedTag.id == tag_id).first()
        if not banned_tag:
            raise HTTPException(status_code=404, detail="Banned tag not found")
        
        tag_name = banned_tag.tag
        
        # Delete banned tag entry
        db.delete(banned_tag)
        db.commit()
        
        logger.info("Tag unbanned successfully", tag=tag_name, unbanned_by=admin_user.email)
        
        return {"message": "Tag unbanned successfully", "tag": tag_name}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error unbanning tag", tag_id=tag_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while unbanning the tag"
        )

