"""Service for filtering spam in comments using banned words."""

import re
from typing import List, Tuple
from sqlalchemy.orm import Session
from ..database.models import BannedWord
import structlog

logger = structlog.get_logger()

class SpamFilterService:
    """Service for detecting spam in comments using banned words."""
    
    def __init__(self):
        self._banned_words_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes cache
    
    def _load_banned_words(self, db: Session) -> List[str]:
        """Load banned words from database with caching."""
        import time
        
        current_time = time.time()
        
        # Check if cache is still valid
        if (self._banned_words_cache is not None and 
            self._cache_timestamp is not None and
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._banned_words_cache
        
        # Load from database
        banned_words = db.query(BannedWord.word).all()
        self._banned_words_cache = [word[0].lower() for word in banned_words]
        self._cache_timestamp = current_time
        
        logger.debug(
            "Loaded banned words",
            count=len(self._banned_words_cache)
        )
        
        return self._banned_words_cache
    
    def check_spam(self, text: str, db: Session) -> Tuple[bool, List[str]]:
        """
        Check if text contains spam/banned words.
        
        Args:
            text: The text to check
            db: Database session
            
        Returns:
            Tuple of (is_spam, matched_words)
        """
        if not text:
            return False, []
        
        banned_words = self._load_banned_words(db)
        text_lower = text.lower()
        
        matched_words = []
        for banned_word in banned_words:
            # Use word boundaries for exact word matching
            pattern = r'\b' + re.escape(banned_word.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matched_words.append(banned_word)
        
        is_spam = len(matched_words) > 0
        
        if is_spam:
            logger.info(
                "Spam detected",
                matched_words=matched_words,
                text_preview=text[:100]
            )
        
        return is_spam, matched_words
    
    def invalidate_cache(self):
        """Invalidate the banned words cache."""
        self._banned_words_cache = None
        self._cache_timestamp = None
        logger.debug("Banned words cache invalidated")

# Global instance
spam_filter_service = SpamFilterService()

