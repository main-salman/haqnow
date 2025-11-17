"""Service for caching comments and annotations."""

import time
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger()

class CommentCacheService:
    """Service for caching comments and annotations to reduce database load."""
    
    def __init__(self):
        # Cache format: {document_id: {"data": [...], "timestamp": float, "sort_order": str}}
        self._comments_cache = {}
        self._annotations_cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
    
    def get_cached_comments(self, document_id: int, sort_order: str = "most_replies") -> Optional[List[Dict[str, Any]]]:
        """
        Get cached comments for a document.
        
        Args:
            document_id: The document ID
            sort_order: Sort order (most_replies, newest, oldest)
            
        Returns:
            Cached comments or None if cache miss/expired
        """
        cache_key = f"{document_id}:{sort_order}"
        cached = self._comments_cache.get(cache_key)
        
        if cached is None:
            return None
        
        # Check if cache is expired
        if time.time() - cached["timestamp"] > self._cache_ttl:
            del self._comments_cache[cache_key]
            return None
        
        # Check if sort order matches
        if cached.get("sort_order") != sort_order:
            return None
        
        logger.debug("Cache hit for comments", document_id=document_id)
        return cached["data"]
    
    def set_cached_comments(self, document_id: int, comments: List[Dict[str, Any]], sort_order: str = "most_replies"):
        """
        Cache comments for a document.
        
        Args:
            document_id: The document ID
            comments: List of comment dictionaries
            sort_order: Sort order used
        """
        cache_key = f"{document_id}:{sort_order}"
        self._comments_cache[cache_key] = {
            "data": comments,
            "timestamp": time.time(),
            "sort_order": sort_order
        }
        logger.debug("Cached comments", document_id=document_id, count=len(comments))
    
    def invalidate_comments_cache(self, document_id: int):
        """Invalidate cache for a specific document."""
        keys_to_remove = [key for key in self._comments_cache.keys() if key.startswith(f"{document_id}:")]
        for key in keys_to_remove:
            del self._comments_cache[key]
        logger.debug("Invalidated comments cache", document_id=document_id)
    
    def get_cached_annotations(self, document_id: int) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached annotations for a document.
        
        Args:
            document_id: The document ID
            
        Returns:
            Cached annotations or None if cache miss/expired
        """
        cached = self._annotations_cache.get(document_id)
        
        if cached is None:
            return None
        
        # Check if cache is expired
        if time.time() - cached["timestamp"] > self._cache_ttl:
            del self._annotations_cache[document_id]
            return None
        
        logger.debug("Cache hit for annotations", document_id=document_id)
        return cached["data"]
    
    def set_cached_annotations(self, document_id: int, annotations: List[Dict[str, Any]]):
        """
        Cache annotations for a document.
        
        Args:
            document_id: The document ID
            annotations: List of annotation dictionaries
        """
        self._annotations_cache[document_id] = {
            "data": annotations,
            "timestamp": time.time()
        }
        logger.debug("Cached annotations", document_id=document_id, count=len(annotations))
    
    def invalidate_annotations_cache(self, document_id: int):
        """Invalidate cache for a specific document."""
        if document_id in self._annotations_cache:
            del self._annotations_cache[document_id]
        logger.debug("Invalidated annotations cache", document_id=document_id)
    
    def cleanup_expired(self):
        """Clean up expired cache entries."""
        current_time = time.time()
        
        # Clean comments cache
        keys_to_remove = []
        for key, cached in self._comments_cache.items():
            if current_time - cached["timestamp"] > self._cache_ttl:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self._comments_cache[key]
        
        # Clean annotations cache
        doc_ids_to_remove = []
        for doc_id, cached in self._annotations_cache.items():
            if current_time - cached["timestamp"] > self._cache_ttl:
                doc_ids_to_remove.append(doc_id)
        for doc_id in doc_ids_to_remove:
            del self._annotations_cache[doc_id]
        
        if keys_to_remove or doc_ids_to_remove:
            logger.info(
                "Cleaned up expired cache entries",
                comments_removed=len(keys_to_remove),
                annotations_removed=len(doc_ids_to_remove)
            )

# Global instance
comment_cache_service = CommentCacheService()

