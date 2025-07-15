"""SQLAlchemy models for FOI Archive database."""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from .database import Base

class Document(Base):
    """Document model for storing FOI documents."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(1000), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    
    # Processing information
    ocr_text = Column(Text, nullable=True)
    generated_tags = Column(JSON, nullable=True, default=list)
    
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
            "file_path": self.file_path,
            "file_url": self.file_url,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "ocr_text": self.ocr_text,
            "generated_tags": self.generated_tags or [],
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "approved_by": self.approved_by,
            "rejected_by": self.rejected_by,
            "rejection_reason": self.rejection_reason
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