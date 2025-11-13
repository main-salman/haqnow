"""Service for tracking document views with time-based rate limiting."""

import time
from typing import Optional
from sqlalchemy.orm import Session
from ..database.models import Document
import structlog

logger = structlog.get_logger()

class ViewTrackingService:
    """Service for tracking document views with privacy-compliant rate limiting."""
    
    def __init__(self):
        # In-memory store for rate limiting (session-based, no user tracking)
        # Format: {document_id: last_view_timestamp}
        self._view_timestamps = {}
        self._rate_limit_seconds = 3600  # 1 hour between views for same document
    
    def should_count_view(self, document_id: int, session_id: str) -> bool:
        """
        Check if a view should be counted based on time-based rate limiting.
        Uses a session identifier (not user-specific) to prevent spam.
        
        Args:
            document_id: The document being viewed
            session_id: Anonymous session identifier (e.g., hash of IP + user-agent)
        
        Returns:
            True if view should be counted, False otherwise
        """
        key = f"{document_id}:{session_id}"
        current_time = time.time()
        
        last_view_time = self._view_timestamps.get(key)
        
        if last_view_time is None:
            # First view for this document/session
            self._view_timestamps[key] = current_time
            return True
        
        # Check if enough time has passed
        time_since_last_view = current_time - last_view_time
        
        if time_since_last_view >= self._rate_limit_seconds:
            self._view_timestamps[key] = current_time
            return True
        
        # Too soon, don't count
        return False
    
    def increment_view_count(
        self, 
        document_id: int, 
        session_id: str,
        db: Session
    ) -> bool:
        """
        Increment view count for a document if rate limit allows.
        
        Args:
            document_id: The document being viewed
            session_id: Anonymous session identifier
            db: Database session
        
        Returns:
            True if view was counted, False if rate limited
        """
        try:
            if not self.should_count_view(document_id, session_id):
                logger.debug(
                    "View not counted (rate limited)",
                    document_id=document_id
                )
                return False
            
            # Increment view count in database
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if document:
                document.view_count = (document.view_count or 0) + 1
                db.commit()
                
                logger.info(
                    "View counted",
                    document_id=document_id,
                    new_count=document.view_count
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                "Error incrementing view count",
                document_id=document_id,
                error=str(e)
            )
            db.rollback()
            return False
    
    def cleanup_old_entries(self, max_age_seconds: int = 7200):
        """
        Clean up old entries from the in-memory rate limit store.
        Call this periodically to prevent memory growth.
        
        Args:
            max_age_seconds: Remove entries older than this (default: 2 hours)
        """
        current_time = time.time()
        keys_to_remove = []
        
        for key, timestamp in self._view_timestamps.items():
            if current_time - timestamp > max_age_seconds:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._view_timestamps[key]
        
        if keys_to_remove:
            logger.info(
                "Cleaned up old view tracking entries",
                removed_count=len(keys_to_remove)
            )

# Global instance
view_tracking_service = ViewTrackingService()

