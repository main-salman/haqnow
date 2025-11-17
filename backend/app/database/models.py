"""SQLAlchemy models for FOI Archive database."""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

# Import pgvector for vector operations (used only in RAG/Postgres)
try:
    from pgvector.sqlalchemy import Vector  # type: ignore
except ImportError:
    Vector = Text  # Fallback

class Document(Base):
    """Document model for storing FOI documents."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Document language and translation support
    document_language = Column(String(10), nullable=False, default="english", index=True)  # Language of original document
    ocr_text_original = Column(Text, nullable=True)  # OCR text in original language
    ocr_text_english = Column(Text, nullable=True)   # OCR text translated to English (if needed)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(1000), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    
    # Processing information
    ocr_text = Column(MEDIUMTEXT, nullable=True)  # Combined/processed OCR text (up to 16MB)
    generated_tags = Column(JSON, nullable=True, default=list)
    search_text = Column(MEDIUMTEXT, nullable=True)  # Combined searchable text for full-text search (up to 16MB)
    embedding = Column(JSON, nullable=True)  # Semantic search embedding vector (384 dimensions)
    ai_summary = Column(Text, nullable=True)  # AI-generated summary (1 paragraph) using Groq API
    
    # Status and workflow
    status = Column(String(50), nullable=False, default="pending", index=True)
    # Status values: pending, processed, approved, rejected
    
    # Upload information - IP addresses removed for privacy compliance
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    
    # Admin actions
    approved_by = Column(String(255), nullable=True)
    rejected_by = Column(String(255), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # View tracking
    view_count = Column(Integer, nullable=False, default=0, index=True)
    hidden_from_top_viewed = Column(Boolean, nullable=False, default=False, index=True)
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "country": self.country,
            "state": self.state,
            "description": self.description,
            "document_language": self.document_language,
            "ocr_text_original": self.ocr_text_original,
            "ocr_text_english": self.ocr_text_english,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "ocr_text": self.ocr_text,
            "generated_tags": self.generated_tags or [],
            "search_text": self.search_text,
            "ai_summary": self.ai_summary,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "approved_by": self.approved_by,
            "rejected_by": self.rejected_by,
            "rejection_reason": self.rejection_reason,
            "view_count": self.view_count,
            "hidden_from_top_viewed": self.hidden_from_top_viewed
        }

class BannedTag(Base):
    """Model for storing banned tags that admins don't want to allow."""
    
    __tablename__ = "banned_tags"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tag = Column(String(100), nullable=False, unique=True, index=True)
    reason = Column(Text, nullable=True)
    banned_by = Column(String(255), nullable=False)
    banned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<BannedTag(id={self.id}, tag='{self.tag}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "tag": self.tag,
            "reason": self.reason,
            "banned_by": self.banned_by,
            "banned_at": self.banned_at.isoformat() if self.banned_at else None
        }

class Translation(Base):
    """Model for storing multilingual content translations."""
    
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(200), nullable=False, index=True)
    language = Column(String(5), nullable=False, index=True)
    value = Column(Text, nullable=False)
    section = Column(String(50), nullable=False, index=True)  # navigation, homepage, search, upload, privacy, general
    updated_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Composite unique constraint on key + language
    __table_args__ = (
        UniqueConstraint('key', 'language', name='unique_key_language'),
    )
    
    def __repr__(self):
        return f"<Translation(id={self.id}, key='{self.key}', language='{self.language}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "key": self.key,
            "language": self.language,
            "value": self.value,
            "section": self.section,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Admin(Base):
    """Model for storing admin users with 2FA support."""
    
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 2FA fields
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
    two_factor_secret = Column(String(32), nullable=True)  # TOTP secret
    backup_codes = Column(JSON, nullable=True, default=list)  # Backup codes array
    
    # Admin management
    is_active = Column(Boolean, nullable=False, default=True)
    is_super_admin = Column(Boolean, nullable=False, default=False)  # Can manage other admins
    created_by = Column(String(255), nullable=True)  # Email of admin who created this admin
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Admin(id={self.id}, email='{self.email}', name='{self.name}')>"
    
    def to_dict(self, include_sensitive=False):
        """Convert model to dictionary."""
        data = {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "two_factor_enabled": self.two_factor_enabled,
            "is_active": self.is_active,
            "is_super_admin": self.is_super_admin,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }
        
        if include_sensitive:
            data.update({
                "two_factor_secret": self.two_factor_secret,
                "backup_codes": self.backup_codes or []
            })
        
        return data

# IMPORTANT: RAG chunk storage belongs in PostgreSQL (app.database.rag_models).
# Do not define the `document_chunks` table in the main MySQL metadata to avoid
# unsupported types like VECTOR(384) on MySQL. The authoritative model lives in
# `app/database/rag_models.py` and is managed separately.

class RAGQuery(Base):
    """Model for logging RAG Q&A interactions for monitoring and improvement."""
    
    __tablename__ = "rag_queries"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    sources_count = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    user_feedback = Column(String(50), nullable=True)  # 'helpful', 'not_helpful', etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<RAGQuery(id={self.id}, query='{self.query_text[:50]}...')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "query_text": self.query_text,
            "answer_text": self.answer_text,
            "confidence_score": self.confidence_score,
            "sources_count": self.sources_count,
            "response_time_ms": self.response_time_ms,
            "user_feedback": self.user_feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class SiteSetting(Base):
    """Model for storing simple site-wide settings as key/value pairs.

    Used for global features like the announcement banner.
    """

    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)  # JSON or plain text string
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<SiteSetting(key='{self.key}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class APIKey(Base):
    """Model for API keys used to authenticate programmatic access.

    We store only a secure hash of the key and never the plaintext.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    key_hash = Column(String(128), nullable=False, unique=True, index=True)
    key_prefix = Column(String(16), nullable=False, index=True)  # first N chars of plaintext for display
    scopes = Column(JSON, nullable=False, default=list)  # e.g., ["upload", "download"]
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(255), nullable=True)  # admin email
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)

    def to_safe_dict(self):
        """Return non-sensitive representation of the API key (without key hash)."""
        return {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "scopes": self.scopes or [],
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
        }

class DocumentComment(Base):
    """Model for anonymous comments on documents."""
    
    __tablename__ = "document_comments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    parent_comment_id = Column(Integer, ForeignKey('document_comments.id', ondelete='CASCADE'), nullable=True, index=True)
    comment_text = Column(Text, nullable=False)
    session_id = Column(String(64), nullable=False, index=True)  # Anonymous session hash
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending, approved, rejected, flagged
    flag_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    replies = relationship("DocumentComment", backref="parent", remote_side=[id], cascade="all, delete")
    
    def __repr__(self):
        return f"<DocumentComment(id={self.id}, document_id={self.document_id}, status='{self.status}')>"
    
    def to_dict(self, include_replies=True):
        """Convert model to dictionary."""
        # Calculate reply_count safely
        reply_count = 0
        if hasattr(self, 'replies') and self.replies is not None:
            try:
                reply_count = len([r for r in self.replies if r.status == 'approved'])
            except (AttributeError, TypeError):
                reply_count = 0
        
        data = {
            "id": self.id,
            "document_id": self.document_id,
            "parent_comment_id": self.parent_comment_id,
            "comment_text": self.comment_text,
            "status": self.status,
            "flag_count": self.flag_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reply_count": reply_count,
        }
        
        if include_replies:
            try:
                if hasattr(self, 'replies') and self.replies is not None:
                    # Only include approved replies
                    approved_replies = [reply for reply in self.replies if hasattr(reply, 'status') and reply.status == 'approved']
                    data["replies"] = [reply.to_dict(include_replies=False) for reply in approved_replies]
                else:
                    data["replies"] = []
            except (AttributeError, TypeError, Exception) as e:
                # If there's any error accessing replies, just set empty list
                data["replies"] = []
        
        return data

class DocumentAnnotation(Base):
    """Model for anonymous annotations/highlights on documents."""
    
    __tablename__ = "document_annotations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)  # Anonymous session hash
    page_number = Column(Integer, nullable=False)
    x = Column(Float, nullable=False)  # X coordinate
    y = Column(Float, nullable=False)  # Y coordinate
    width = Column(Float, nullable=False)  # Width of highlight
    height = Column(Float, nullable=False)  # Height of highlight
    highlighted_text = Column(Text, nullable=True)  # The text that was highlighted
    annotation_note = Column(Text, nullable=True)  # User's note/comment on the highlight
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<DocumentAnnotation(id={self.id}, document_id={self.document_id}, page={self.page_number})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "page_number": self.page_number,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "highlighted_text": self.highlighted_text,
            "annotation_note": self.annotation_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class BannedWord(Base):
    """Model for storing banned words/phrases for spam filtering."""
    
    __tablename__ = "banned_words"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    word = Column(String(200), nullable=False, unique=True, index=True)  # Word or phrase
    reason = Column(Text, nullable=True)
    banned_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<BannedWord(id={self.id}, word='{self.word}')>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "word": self.word,
            "reason": self.reason,
            "banned_by": self.banned_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }