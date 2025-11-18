"""API endpoints for anonymous comments and annotations on documents."""

import hashlib
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_
from datetime import datetime
import structlog

from app.database import get_db
from app.database.models import Document, DocumentComment, DocumentAnnotation, BannedWord
from app.services.spam_filter_service import spam_filter_service
from app.services.comment_rate_limit_service import comment_rate_limit_service
from app.services.comment_cache_service import comment_cache_service
from app.auth.user import AdminUser

logger = structlog.get_logger()

router = APIRouter()

def get_anonymous_session_id(request: Request) -> str:
    """Generate anonymous session identifier."""
    user_agent = request.headers.get("user-agent", "unknown")
    session_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]
    return session_hash

# Pydantic models
class CommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=10, max_length=5000)
    parent_comment_id: Optional[int] = None

class CommentResponse(BaseModel):
    id: int
    document_id: int
    parent_comment_id: Optional[int]
    comment_text: str
    status: str
    flag_count: int
    created_at: str
    reply_count: int
    replies: Optional[List['CommentResponse']] = None

class AnnotationCreate(BaseModel):
    page_number: int = Field(..., ge=1)
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    highlighted_text: Optional[str] = None
    annotation_note: Optional[str] = Field(None, max_length=1000)

class AnnotationResponse(BaseModel):
    id: int
    document_id: int
    page_number: int
    x: float
    y: float
    width: float
    height: float
    highlighted_text: Optional[str]
    annotation_note: Optional[str]
    created_at: str

CommentResponse.model_rebuild()

# Comment endpoints
@router.post("/documents/{document_id}/comments", response_model=CommentResponse)
async def create_comment(
    document_id: int,
    comment_data: CommentCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new anonymous comment on a document."""
    # Verify document exists and is approved
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.status == "approved"
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check comment limit (100 per document)
    comment_count = db.query(func.count(DocumentComment.id)).filter(
        DocumentComment.document_id == document_id,
        DocumentComment.status.in_(['pending', 'approved'])
    ).scalar()
    
    if comment_count >= 100:
        raise HTTPException(status_code=400, detail="Comment limit reached")
    
    # Check rate limit
    session_id = get_anonymous_session_id(request)
    allowed, seconds_remaining = comment_rate_limit_service.check_rate_limit(document_id, session_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please wait {int(seconds_remaining)} seconds."
        )
    
    # Check spam
    is_spam, matched_words = spam_filter_service.check_spam(comment_data.comment_text, db)
    if is_spam:
        raise HTTPException(
            status_code=400,
            detail="Comment contains inappropriate content"
        )
    
    # Validate parent comment if replying
    if comment_data.parent_comment_id:
        parent = db.query(DocumentComment).filter(
            DocumentComment.id == comment_data.parent_comment_id,
            DocumentComment.document_id == document_id,
            DocumentComment.status == "approved"
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    # Create comment (public by default - auto-approved)
    comment = DocumentComment(
        document_id=document_id,
        parent_comment_id=comment_data.parent_comment_id,
        comment_text=comment_data.comment_text,
        session_id=session_id,
        status='approved'  # Public by default - comments are visible immediately
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Invalidate cache
    comment_cache_service.invalidate_comments_cache(document_id)
    
    logger.info(
        "Comment created",
        comment_id=comment.id,
        document_id=document_id,
        is_reply=comment_data.parent_comment_id is not None
    )
    
    return CommentResponse(**comment.to_dict(include_replies=False))

@router.get("/documents/{document_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    document_id: int,
    sort_order: str = Query("most_replies", regex="^(most_replies|newest|oldest)$"),
    db: Session = Depends(get_db)
):
    """Get all approved comments for a document."""
    # Check cache
    cached = comment_cache_service.get_cached_comments(document_id, sort_order)
    if cached is not None:
        return cached
    
    # Verify document exists
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.status == "approved"
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get all approved comments for this document (including replies)
    all_document_comments = db.query(DocumentComment).filter(
        DocumentComment.document_id == document_id,
        DocumentComment.status == "approved"
    ).all()
    
    # Build a map of comment_id -> list of replies (don't assign to SQLAlchemy relationship)
    replies_map = {}
    for comment in all_document_comments:
        if comment.parent_comment_id:
            if comment.parent_comment_id not in replies_map:
                replies_map[comment.parent_comment_id] = []
            replies_map[comment.parent_comment_id].append(comment)
    
    # Attach replies to ALL comments (including nested replies)
    for comment in all_document_comments:
        comment._replies_list = replies_map.get(comment.id, [])
    
    # Get top-level comments only (no parent)
    all_comments = [c for c in all_document_comments if c.parent_comment_id is None]
    
    # Helper function to count all nested replies recursively
    def count_all_replies(comment):
        replies_list = getattr(comment, '_replies_list', [])
        count = len(replies_list)
        for reply in replies_list:
            count += count_all_replies(reply)
        return count
    
    # Apply sorting
    if sort_order == "most_replies":
        # Sort by reply count (including nested replies)
        comments = sorted(
            all_comments,
            key=lambda c: (count_all_replies(c), c.created_at),
            reverse=True
        )
    elif sort_order == "newest":
        comments = sorted(all_comments, key=lambda c: c.created_at, reverse=True)
    else:  # oldest
        comments = sorted(all_comments, key=lambda c: c.created_at)
    
    # Convert to dict with replies (only include approved replies)
    result = []
    for comment in comments:
        try:
            comment_dict = comment.to_dict(include_replies=True)
            result.append(CommentResponse(**comment_dict))
        except Exception as e:
            logger.error(f"Error converting comment {comment.id} to dict: {e}")
            # Fallback: create dict without replies
            comment_dict = comment.to_dict(include_replies=False)
            result.append(CommentResponse(**comment_dict))
    
    # Cache result (convert Pydantic models to dict)
    cache_data = []
    for comment_response in result:
        cache_data.append(comment_response.model_dump() if hasattr(comment_response, 'model_dump') else comment_response.dict())
    comment_cache_service.set_cached_comments(document_id, cache_data, sort_order)
    
    return result

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete own comment (hard delete)."""
    session_id = get_anonymous_session_id(request)
    
    comment = db.query(DocumentComment).filter(
        DocumentComment.id == comment_id,
        DocumentComment.session_id == session_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")
    
    document_id = comment.document_id
    
    # Hard delete
    db.delete(comment)
    db.commit()
    
    # Invalidate cache
    comment_cache_service.invalidate_comments_cache(document_id)
    
    logger.info("Comment deleted", comment_id=comment_id, document_id=document_id)
    
    return {"message": "Comment deleted successfully"}

@router.post("/comments/{comment_id}/flag")
async def flag_comment(
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Flag a comment for moderation."""
    comment = db.query(DocumentComment).filter(
        DocumentComment.id == comment_id,
        DocumentComment.status.in_(['pending', 'approved'])
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Increment flag count
    comment.flag_count += 1
    
    # Auto-hide if 3+ flags
    if comment.flag_count >= 3:
        comment.status = 'flagged'
    
    db.commit()
    
    logger.info("Comment flagged", comment_id=comment_id, flag_count=comment.flag_count)
    
    return {"message": "Comment flagged successfully", "flag_count": comment.flag_count}

# Annotation endpoints
@router.post("/documents/{document_id}/annotations", response_model=AnnotationResponse)
async def create_annotation(
    document_id: int,
    annotation_data: AnnotationCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new annotation/highlight on a document."""
    # Verify document exists
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.status == "approved"
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check rate limit
    session_id = get_anonymous_session_id(request)
    allowed, seconds_remaining = comment_rate_limit_service.check_rate_limit(document_id, session_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Please wait {int(seconds_remaining)} seconds."
        )
    
    # Check spam if annotation note provided
    if annotation_data.annotation_note:
        is_spam, matched_words = spam_filter_service.check_spam(annotation_data.annotation_note, db)
        if is_spam:
            raise HTTPException(
                status_code=400,
                detail="Annotation note contains inappropriate content"
            )
    
    # Create annotation
    annotation = DocumentAnnotation(
        document_id=document_id,
        session_id=session_id,
        page_number=annotation_data.page_number,
        x=annotation_data.x,
        y=annotation_data.y,
        width=annotation_data.width,
        height=annotation_data.height,
        highlighted_text=annotation_data.highlighted_text,
        annotation_note=annotation_data.annotation_note
    )
    
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    
    # Invalidate cache
    comment_cache_service.invalidate_annotations_cache(document_id)
    
    logger.info("Annotation created", annotation_id=annotation.id, document_id=document_id)
    
    return AnnotationResponse(**annotation.to_dict())

@router.get("/documents/{document_id}/annotations", response_model=List[AnnotationResponse])
async def get_annotations(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get all annotations for a document."""
    # Check cache
    cached = comment_cache_service.get_cached_annotations(document_id)
    if cached is not None:
        return cached
    
    # Verify document exists
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.status == "approved"
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get all annotations
    annotations = db.query(DocumentAnnotation).filter(
        DocumentAnnotation.document_id == document_id
    ).order_by(asc(DocumentAnnotation.page_number), asc(DocumentAnnotation.created_at)).all()
    
    result = [AnnotationResponse(**ann.to_dict()) for ann in annotations]
    
    # Cache result (convert Pydantic models to dict)
    cache_data = []
    for annotation_response in result:
        cache_data.append(annotation_response.model_dump() if hasattr(annotation_response, 'model_dump') else annotation_response.dict())
    comment_cache_service.set_cached_annotations(document_id, cache_data)
    
    return result

@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete own annotation (hard delete)."""
    session_id = get_anonymous_session_id(request)
    
    annotation = db.query(DocumentAnnotation).filter(
        DocumentAnnotation.id == annotation_id,
        DocumentAnnotation.session_id == session_id
    ).first()
    
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found or not authorized")
    
    document_id = annotation.document_id
    
    # Hard delete
    db.delete(annotation)
    db.commit()
    
    # Invalidate cache
    comment_cache_service.invalidate_annotations_cache(document_id)
    
    logger.info("Annotation deleted", annotation_id=annotation_id, document_id=document_id)
    
    return {"message": "Annotation deleted successfully"}

# Admin endpoints
@router.get("/admin/comments/pending", response_model=List[CommentResponse])
async def get_pending_comments(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Get all pending and flagged comments for moderation."""
    comments = db.query(DocumentComment).filter(
        DocumentComment.status.in_(['pending', 'flagged'])
    ).order_by(desc(DocumentComment.created_at)).all()
    
    return [CommentResponse(**comment.to_dict(include_replies=False)) for comment in comments]

@router.get("/admin/comments/all", response_model=List[CommentResponse])
async def get_all_comments(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Get all comments (for admin management), sorted by document_id then created_at."""
    comments = db.query(DocumentComment).order_by(
        DocumentComment.document_id,
        desc(DocumentComment.created_at)
    ).all()
    
    return [CommentResponse(**comment.to_dict(include_replies=False)) for comment in comments]

@router.delete("/admin/comments/{comment_id}")
async def admin_delete_comment(
    comment_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Admin endpoint to delete any comment."""
    comment = db.query(DocumentComment).filter(DocumentComment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    document_id = comment.document_id
    
    # Hard delete: remove comment and all its replies (cascade delete)
    db.delete(comment)
    db.commit()
    
    # Invalidate cache
    comment_cache_service.invalidate_comments_cache(document_id)
    
    logger.info("Comment deleted by admin", comment_id=comment_id, document_id=document_id, admin=admin_user.email)
    
    return {"message": "Comment deleted successfully"}

@router.post("/admin/comments/{comment_id}/moderate")
async def moderate_comment(
    comment_id: int,
    admin_user: AdminUser,
    action: str = Query(..., regex="^(approve|reject)$"),
    db: Session = Depends(get_db)
):
    """Approve or reject a comment. Reject performs a hard delete."""
    comment = db.query(DocumentComment).filter(DocumentComment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    document_id = comment.document_id
    
    if action == "approve":
        comment.status = "approved"
        db.commit()
    else:
        # Hard delete: remove comment and all its replies (cascade delete)
        db.delete(comment)
        db.commit()
    
    # Invalidate cache
    comment_cache_service.invalidate_comments_cache(document_id)
    
    logger.info("Comment moderated", comment_id=comment_id, action=action, admin=admin_user.email)
    
    return {"message": f"Comment {action}d successfully"}

# Banned words management endpoints
@router.get("/admin/banned-words", response_model=List[dict])
async def get_banned_words(
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Get all banned words."""
    banned_words = db.query(BannedWord).order_by(asc(BannedWord.word)).all()
    return [word.to_dict() for word in banned_words]

@router.post("/admin/banned-words")
async def add_banned_word(
    admin_user: AdminUser,
    word: str = Query(..., min_length=1, max_length=200),
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Add a banned word."""
    # Check if already exists
    existing = db.query(BannedWord).filter(
        func.lower(BannedWord.word) == word.lower()
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Word already banned")
    
    banned_word = BannedWord(
        word=word.lower(),
        reason=reason,
        banned_by=admin_user.email
    )
    
    db.add(banned_word)
    db.commit()
    db.refresh(banned_word)
    
    # Invalidate spam filter cache
    spam_filter_service.invalidate_cache()
    
    logger.info("Banned word added", word=word, admin=admin_user.email)
    
    return {"message": "Banned word added successfully", "banned_word": banned_word.to_dict()}

@router.delete("/admin/banned-words/{word_id}")
async def delete_banned_word(
    word_id: int,
    admin_user: AdminUser,
    db: Session = Depends(get_db)
):
    """Delete a banned word."""
    banned_word = db.query(BannedWord).filter(BannedWord.id == word_id).first()
    
    if not banned_word:
        raise HTTPException(status_code=404, detail="Banned word not found")
    
    db.delete(banned_word)
    db.commit()
    
    # Invalidate spam filter cache
    spam_filter_service.invalidate_cache()
    
    logger.info("Banned word deleted", word_id=word_id, admin=admin_user.email)
    
    return {"message": "Banned word deleted successfully"}

