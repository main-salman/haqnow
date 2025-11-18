"""Service for rate limiting comments and annotations."""

import time
from typing import Optional, Tuple
import structlog

logger = structlog.get_logger()

class CommentRateLimitService:
    """Service for rate limiting comments and annotations per document."""
    
    def __init__(self):
        # In-memory store for rate limiting (session-based, no user tracking)
        # Format: {f"{document_id}:{session_id}": last_action_timestamp}
        self._action_timestamps = {}
        self._rate_limit_seconds = 60  # 60 seconds (1 minute) between actions
    
    def check_rate_limit(self, document_id: int, session_id: str) -> Tuple[bool, Optional[float]]:
        """
        Check if action is allowed based on rate limiting.
        
        Args:
            document_id: The document ID
            session_id: Anonymous session identifier
            
        Returns:
            Tuple of (allowed, seconds_until_allowed)
        """
        key = f"{document_id}:{session_id}"
        current_time = time.time()
        
        last_action_time = self._action_timestamps.get(key)
        
        if last_action_time is None:
            # First action for this document/session
            self._action_timestamps[key] = current_time
            return True, None
        
        # Check if enough time has passed
        time_since_last_action = current_time - last_action_time
        
        if time_since_last_action >= self._rate_limit_seconds:
            self._action_timestamps[key] = current_time
            return True, None
        
        # Too soon, rate limited
        seconds_remaining = self._rate_limit_seconds - time_since_last_action
        logger.debug(
            "Rate limit exceeded",
            document_id=document_id,
            seconds_remaining=seconds_remaining
        )
        return False, seconds_remaining
    
    def cleanup_old_entries(self, max_age_seconds: int = 7200):
        """
        Clean up old entries from the in-memory rate limit store.
        
        Args:
            max_age_seconds: Remove entries older than this (default: 2 hours)
        """
        current_time = time.time()
        keys_to_remove = []
        
        for key, timestamp in self._action_timestamps.items():
            if current_time - timestamp > max_age_seconds:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._action_timestamps[key]
        
        if keys_to_remove:
            logger.info(
                "Cleaned up old rate limit entries",
                removed_count=len(keys_to_remove)
            )

# Global instance
comment_rate_limit_service = CommentRateLimitService()

