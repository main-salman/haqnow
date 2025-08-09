import json
import re
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
import os
import structlog
import requests
from urllib.parse import urlparse

# Import rate limiting, auth, and database
from app.middleware.rate_limit import check_download_rate_limit, record_download
from app.auth.user import AdminUser
from app.database import get_db, Document, BannedTag
from app.services.semantic_search_service import semantic_search_service

logger = structlog.get_logger()

router = APIRouter()

def filter_banned_words_from_text(text: str, banned_words: List[str]) -> str:
    """Filter banned words from text content in search results."""
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
        logger.error("Error filtering banned words from search result", error=str(e))
        return text

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
    document_language: Optional[str] = None  # Language of the original document
    has_arabic_text: bool = False  # Whether Arabic text is available
    has_english_translation: bool = False  # Whether English translation is available
    similarity_score: Optional[float] = None  # For semantic search results
    search_type: Optional[str] = None  # 'semantic', 'keyword', or 'hybrid'

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
    search_type: str = Query("hybrid", description="Search type: 'semantic', 'keyword', or 'hybrid'"),
    db: Session = Depends(get_db)
):
    """
    Search documents by text content and tags.
    Returns only approved documents.
    """
    
    try:
        search_query = q.strip() if q else ""
        documents_data = []
        total_count = 0
        
        # Choose search strategy based on search_type parameter
        if not search_query:
            # No search query - return all documents by date
            query_builder = db.query(Document).filter(Document.status == "approved")
            
            # Apply filters
            if country:
                query_builder = query_builder.filter(Document.country == country)
            if state:
                query_builder = query_builder.filter(Document.state == state)
            
            total_count = query_builder.count()
            
            # Apply pagination and ordering
            offset = (page - 1) * per_page
            documents_data = query_builder.order_by(Document.created_at.desc()).offset(offset).limit(per_page).all()
            
            logger.info("No search query, returning all documents", 
                       total_count=total_count,
                       search_type="none")
        
        elif search_type == "semantic":
            # Pure semantic search
            if semantic_search_service.is_available():
                semantic_results = semantic_search_service.search_similar_documents(
                    search_query, db, limit=per_page * 3  # Get more for filtering
                )
                
                # Apply country/state filters
                if country or state:
                    semantic_results = [
                        doc for doc in semantic_results 
                        if (not country or doc.get('country') == country) and 
                           (not state or doc.get('state') == state)
                    ]
                
                # Apply pagination
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                paginated_results = semantic_results[start_idx:end_idx]
                
                total_count = len(semantic_results)
                documents_data = paginated_results  # These are already dictionaries
                
                logger.info("Semantic search completed", 
                           query=search_query,
                           results_found=len(semantic_results),
                           search_type="semantic")
            else:
                logger.warning("Semantic search not available, falling back to keyword search")
                search_type = "keyword"  # Fallback to keyword search
        
        if search_type == "keyword" or (search_type == "semantic" and not semantic_search_service.is_available()):
            # Traditional keyword search
            query_builder = db.query(Document).filter(Document.status == "approved")
            
            try:
                # Full-text search on search_text column
                fulltext_condition = func.match(Document.search_text).against(
                    search_query, 
                    func.text("IN NATURAL LANGUAGE MODE")
                )
                
                # Fallback search conditions
                fallback_conditions = [
                    Document.title.ilike(f"%{search_query}%"),
                    Document.country.ilike(f"%{search_query}%"),
                    Document.state.ilike(f"%{search_query}%"),
                    func.json_search(Document.generated_tags, 'one', f"%{search_query}%").isnot(None)
                ]
                
                combined_condition = or_(fulltext_condition, or_(*fallback_conditions))
                query_builder = query_builder.filter(combined_condition)
                
                logger.info("Using keyword search", query=search_query, search_type="keyword")
                
            except Exception as search_error:
                logger.warning("Full-text search failed, using LIKE search", error=str(search_error))
                search_conditions = [
                    Document.title.ilike(f"%{search_query}%"),
                    Document.description.ilike(f"%{search_query}%"),
                    Document.ocr_text.ilike(f"%{search_query}%"),
                    Document.country.ilike(f"%{search_query}%"),
                    Document.state.ilike(f"%{search_query}%"),
                    func.json_search(Document.generated_tags, 'one', f"%{search_query}%").isnot(None)
                ]
                query_builder = query_builder.filter(or_(*search_conditions))
            
            # Apply filters
            if country:
                query_builder = query_builder.filter(Document.country == country)
            if state:
                query_builder = query_builder.filter(Document.state == state)
            
            total_count = query_builder.count()
            
            # Apply pagination and ordering
            offset = (page - 1) * per_page
            query_builder = query_builder.order_by(Document.created_at.desc()).offset(offset).limit(per_page)
            documents_data = query_builder.all()
        
        elif search_type == "hybrid":
            # Hybrid search: combine semantic and keyword results
            all_results = []
            
            # Get semantic results if available
            if semantic_search_service.is_available():
                semantic_results = semantic_search_service.search_similar_documents(
                    search_query, db, limit=per_page * 2
                )
                for result in semantic_results:
                    result['search_type'] = 'semantic'
                all_results.extend(semantic_results)
                
                logger.info("Hybrid search: semantic results", count=len(semantic_results))
            
            # Get keyword results
            query_builder = db.query(Document).filter(Document.status == "approved")
            
            try:
                fulltext_condition = func.match(Document.search_text).against(
                    search_query, 
                    func.text("IN NATURAL LANGUAGE MODE")
                )
                fallback_conditions = [
                    Document.title.ilike(f"%{search_query}%"),
                    Document.country.ilike(f"%{search_query}%"),
                    Document.state.ilike(f"%{search_query}%"),
                    func.json_search(Document.generated_tags, 'one', f"%{search_query}%").isnot(None)
                ]
                combined_condition = or_(fulltext_condition, or_(*fallback_conditions))
                query_builder = query_builder.filter(combined_condition)
                
            except Exception:
                search_conditions = [
                    Document.title.ilike(f"%{search_query}%"),
                    Document.description.ilike(f"%{search_query}%"),
                    Document.ocr_text.ilike(f"%{search_query}%"),
                    func.json_search(Document.generated_tags, 'one', f"%{search_query}%").isnot(None)
                ]
                query_builder = query_builder.filter(or_(*search_conditions))
            
            # Apply filters for keyword search
            if country:
                query_builder = query_builder.filter(Document.country == country)
            if state:
                query_builder = query_builder.filter(Document.state == state)
            
            keyword_docs = query_builder.limit(per_page * 2).all()
            keyword_results = []
            for doc in keyword_docs:
                doc_dict = doc.to_dict()
                doc_dict['search_type'] = 'keyword'
                doc_dict['similarity_score'] = None
                keyword_results.append(doc_dict)
            
            all_results.extend(keyword_results)
            
            logger.info("Hybrid search: keyword results", count=len(keyword_results))
            
            # Remove duplicates (prefer semantic results)
            seen_ids = set()
            unique_results = []
            for result in all_results:
                doc_id = result['id']
                if doc_id not in seen_ids:
                    seen_ids.add(doc_id)
                    unique_results.append(result)
            
            # Apply country/state filters to all results
            if country or state:
                unique_results = [
                    doc for doc in unique_results 
                    if (not country or doc.get('country') == country) and 
                       (not state or doc.get('state') == state)
                ]
            
            # Sort by similarity score (semantic first), then by date
            unique_results.sort(key=lambda x: (
                x.get('similarity_score', 0) if x.get('search_type') == 'semantic' else 0,
                x.get('created_at', '')
            ), reverse=True)
            
            # Apply pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_results = unique_results[start_idx:end_idx]
            
            total_count = len(unique_results)
            documents_data = paginated_results  # These are already dictionaries
            
            logger.info("Hybrid search completed", 
                       total_results=len(unique_results),
                       semantic_count=len([r for r in unique_results if r.get('search_type') == 'semantic']),
                       keyword_count=len([r for r in unique_results if r.get('search_type') == 'keyword']),
                       search_type="hybrid")
        
        # Get banned words for filtering search results
        banned_words = []
        try:
            banned_tags = db.query(BannedTag).all()
            banned_words = [tag.tag.lower() for tag in banned_tags]
        except Exception as e:
            logger.warning("Failed to retrieve banned words for search filtering", error=str(e))
        
        # Convert to response format and filter banned words from results
        documents = []
        for doc in documents_data:
            # Handle both Document objects (from keyword search) and dictionaries (from semantic search)
            if hasattr(doc, 'to_dict'):
                doc_dict = doc.to_dict()
            else:
                doc_dict = doc  # Already a dictionary from semantic search
            
            # Filter banned words from OCR text and tags in search results
            if banned_words:
                if doc_dict.get('ocr_text'):
                    doc_dict['ocr_text'] = filter_banned_words_from_text(doc_dict['ocr_text'], banned_words)
                
                if doc_dict.get('generated_tags'):
                    filtered_tags = []
                    for tag in doc_dict['generated_tags']:
                        if tag.lower() not in banned_words:
                            filtered_tags.append(tag)
                    doc_dict['generated_tags'] = filtered_tags
            
            # Add language information and availability flags
            document_language = doc_dict.get('document_language', 'english')
            has_arabic_text = bool(doc_dict.get('ocr_text_original'))
            has_english_translation = bool(doc_dict.get('ocr_text_english'))
            
            # For Arabic documents, prioritize English translation in search results
            if document_language == 'arabic':
                doc_dict['has_arabic_text'] = has_arabic_text
                doc_dict['has_english_translation'] = has_english_translation
                
                # Show English translation instead of garbled Arabic OCR in search results
                if has_english_translation:
                    doc_dict['ocr_text'] = doc_dict.get('ocr_text_english', doc_dict.get('ocr_text', ''))
                elif doc_dict.get('ocr_text_original'):
                    # If no English translation but has original Arabic, show it
                    doc_dict['ocr_text'] = doc_dict.get('ocr_text_original', doc_dict.get('ocr_text', ''))
                # else keep the existing ocr_text (fallback)
            else:
                # For non-Arabic multilingual documents, check for translations
                doc_dict['has_arabic_text'] = False
                doc_dict['has_english_translation'] = has_english_translation
                
                # For non-English documents, prioritize English translation in search results
                if document_language != 'english' and has_english_translation:
                    doc_dict['ocr_text'] = doc_dict.get('ocr_text_english', doc_dict.get('ocr_text', ''))
                elif document_language != 'english' and doc_dict.get('ocr_text_original'):
                    # If no English translation but has original text, show it
                    doc_dict['ocr_text'] = doc_dict.get('ocr_text_original', doc_dict.get('ocr_text', ''))
                # else keep the existing ocr_text (fallback for English documents)
            
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
    language: str = Query(default="original", description="Language version: 'original', 'english', or the document's original language code"),
    db: Session = Depends(get_db)
):
    """
    Download a document file directly through the server.
    For multilingual documents, supports downloading original language text or English translation.
    This masks the S3 URL and shows the website URL instead.
    Rate limited to prevent abuse.
    """
    
    # Apply rate limit only for original PDF downloads to avoid blocking text downloads
    try:
        if language in (None, "original"):
            check_download_rate_limit(request)
    except Exception:
        # Bubble up HTTPException from rate limiter as-is
        raise
    
    try:
        # Get document from database
        document = db.query(Document).filter(
            and_(Document.id == document_id, Document.status == "approved")
        ).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Determine which content to serve based on language parameter and document language
        document_language = getattr(document, 'document_language', 'english')
        
        # Import multilingual service to check supported languages
        from app.services.multilingual_ocr_service import multilingual_ocr_service
        supported_languages = multilingual_ocr_service.get_supported_languages()
        
        # Check if this is a multilingual document (has both original and English text)
        has_multilingual_content = (
            hasattr(document, 'ocr_text_original') and document.ocr_text_original and
            hasattr(document, 'ocr_text_english') and document.ocr_text_english and
            document.ocr_text_original != document.ocr_text_english
        )
        
        if has_multilingual_content:
            if language == "english":
                # Download English translation
                english_text = getattr(document, 'ocr_text_english', None)
                if not english_text:
                    raise HTTPException(
                        status_code=404, 
                        detail="English translation not available for this document"
                    )
                # Create a text file with English translation
                return create_text_download_response(
                    english_text, 
                    f"{document.title}_english.txt",
                    document_id
                )
            elif language == document_language.lower() or language in [doc_lang.lower() for doc_lang in supported_languages.keys()]:
                # Download original language text
                original_text = getattr(document, 'ocr_text_original', None)
                if not original_text:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Original {document_language} text not available for this document"
                    )
                # Create a text file with original language text
                return create_text_download_response(
                    original_text, 
                    f"{document.title}_{document_language.lower()}.txt",
                    document_id
                )
            # else language == "original" - download the original PDF file
        
        # Default behavior: download original file
        file_path = document.file_path
        
        if not file_path:
            raise HTTPException(status_code=400, detail="Document file not available")
        
        # Get S3 service
        from app.services.s3_service import s3_service
        
        # Generate download URL (used internally to fetch file)
        download_url = s3_service.get_download_url(file_path)
        
        if not download_url:
            raise HTTPException(status_code=500, detail="Failed to generate download URL")
        
        # Record download only for original PDFs
        if language in (None, "original"):
            record_download(request)

        # Fetch file from S3 and stream it to user
        try:
            # Get file from S3
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            # Extract filename from file_path
            filename = os.path.basename(file_path)
            
            # Determine content type based on file extension
            content_type = "application/octet-stream"  # Default
            if filename.lower().endswith('.pdf'):
                content_type = "application/pdf"
            elif filename.lower().endswith(('.jpg', '.jpeg')):
                content_type = "image/jpeg"
            elif filename.lower().endswith('.png'):
                content_type = "image/png"
            elif filename.lower().endswith('.gif'):
                content_type = "image/gif"
            elif filename.lower().endswith('.doc'):
                content_type = "application/msword"
            elif filename.lower().endswith('.docx'):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename.lower().endswith('.xls'):
                content_type = "application/vnd.ms-excel"
            elif filename.lower().endswith('.xlsx'):
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif filename.lower().endswith('.txt'):
                content_type = "text/plain"
            elif filename.lower().endswith('.csv'):
                content_type = "text/csv"
            
            # Create streaming response
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            logger.info("Document download proxied successfully", 
                   document_id=document_id,
                   filename=filename,
                   language=language)
            
            return StreamingResponse(
                generate(),
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename=\"{filename}\"",
                    "Content-Length": str(response.headers.get("content-length", "")),
                    "Cache-Control": "private, max-age=0, no-cache, no-store, must-revalidate"
                }
            )
            
        except requests.RequestException as req_error:
            logger.error("Error fetching file from S3", document_id=document_id, error=str(req_error))
            raise HTTPException(status_code=500, detail="Failed to fetch document file")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error downloading document", document_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="An error occurred while downloading the document"
        )

def create_text_download_response(text_content: str, filename: str, document_id: int) -> StreamingResponse:
    """
    Create a StreamingResponse for text content download.
    Used for Arabic/English text versions of documents.
    """
    try:
        # Encode text as UTF-8 bytes
        text_bytes = text_content.encode('utf-8')
        
        # Create streaming response
        def generate():
            yield text_bytes
        
        logger.info("Text download created successfully", 
                   document_id=document_id,
                   filename=filename,
                   text_length=len(text_content))
        
        return StreamingResponse(
            generate(),
            media_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(text_bytes)),
                "Cache-Control": "private, max-age=0, no-cache, no-store, must-revalidate"
            }
        )
        
    except Exception as e:
        logger.error("Error creating text download response", 
                   document_id=document_id, 
                   filename=filename, 
                   error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to create text download"
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

