"""Rate limiting middleware for document uploads."""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis
import os

# Redis configuration for rate limiting
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
UPLOAD_TIMEOUT_SECONDS = int(os.getenv("UPLOAD_TIMEOUT_SECONDS", "20"))  # 20 seconds

# In-memory fallback if Redis is not available
_memory_store: Dict[str, float] = {}

class RateLimitMiddleware:
    """Rate limiting middleware for document uploads."""
    
    def __init__(self):
        self.redis_client = None
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            self.redis_client.ping()
        except Exception as e:
            print(f"Redis connection failed, using in-memory store: {e}")
            self.redis_client = None
    
    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting - using session-based approach."""
        # Use session-based rate limiting instead of IP-based
        # Generate a simple time-based bucket for global rate limiting
        import time
        # Create 2-minute time buckets for global rate limiting
        bucket_id = int(time.time() / 120)  # 2 minutes = 120 seconds
        return f"global_bucket_{bucket_id}"
    
    def check_rate_limit(self, client_id: str, endpoint: str = "upload") -> Optional[float]:
        """Check if client is rate limited. Returns remaining time if limited, None if allowed."""
        key = f"rate_limit:{endpoint}:{client_id}"
        current_time = time.time()
        
        if self.redis_client:
            try:
                last_upload = self.redis_client.get(key)
                if last_upload:
                    last_upload_time = float(last_upload)
                    time_passed = current_time - last_upload_time
                    if time_passed < UPLOAD_TIMEOUT_SECONDS:
                        return UPLOAD_TIMEOUT_SECONDS - time_passed
                return None
            except Exception as e:
                print(f"Redis error: {e}")
                # Fall back to memory store
                return self._check_memory_rate_limit(client_id, endpoint, current_time)
        else:
            return self._check_memory_rate_limit(client_id, endpoint, current_time)
    
    def _check_memory_rate_limit(self, client_id: str, endpoint: str, current_time: float) -> Optional[float]:
        """Check rate limit using in-memory store."""
        key = f"{endpoint}:{client_id}"
        if key in _memory_store:
            last_upload_time = _memory_store[key]
            time_passed = current_time - last_upload_time
            if time_passed < UPLOAD_TIMEOUT_SECONDS:
                return UPLOAD_TIMEOUT_SECONDS - time_passed
        return None
    
    def record_request(self, client_id: str, endpoint: str = "upload") -> None:
        """Record a request timestamp for rate limiting."""
        key = f"rate_limit:{endpoint}:{client_id}"
        current_time = time.time()
        
        if self.redis_client:
            try:
                self.redis_client.setex(key, UPLOAD_TIMEOUT_SECONDS, current_time)
                return
            except Exception as e:
                print(f"Redis error: {e}")
        
        # Fall back to memory store
        memory_key = f"{endpoint}:{client_id}"
        _memory_store[memory_key] = current_time
        
        # Clean up old entries in memory store
        self._cleanup_memory_store()
    
    def _cleanup_memory_store(self) -> None:
        """Clean up old entries from memory store."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, timestamp in _memory_store.items():
            if current_time - timestamp > UPLOAD_TIMEOUT_SECONDS:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del _memory_store[key]

# Global rate limiter instance
rate_limiter = RateLimitMiddleware()

def check_upload_rate_limit(request: Request) -> None:
    """Check if upload is rate limited and raise HTTPException if so."""
    client_id = rate_limiter.get_client_identifier(request)
    remaining_time = rate_limiter.check_rate_limit(client_id, "upload")
    
    if remaining_time is not None:
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        
        if minutes > 0:
            time_text = f"{minutes} minute{'s' if minutes != 1 else ''} and {seconds} second{'s' if seconds != 1 else ''}"
        else:
            time_text = f"{seconds} second{'s' if seconds != 1 else ''}"
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {time_text} before uploading another document. This helps us maintain service quality for everyone."
        )

def check_download_rate_limit(request: Request) -> None:
    """Check if download is rate limited and raise HTTPException if so."""
    client_id = rate_limiter.get_client_identifier(request)
    remaining_time = rate_limiter.check_rate_limit(client_id, "download")
    
    if remaining_time is not None:
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        
        if minutes > 0:
            time_text = f"{minutes} minute{'s' if minutes != 1 else ''} and {seconds} second{'s' if seconds != 1 else ''}"
        else:
            time_text = f"{seconds} second{'s' if seconds != 1 else ''}"
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {time_text} before downloading another document. This helps us prevent server overload."
        )

def record_upload(request: Request) -> None:
    """Record an upload for rate limiting."""
    client_id = rate_limiter.get_client_identifier(request)
    rate_limiter.record_request(client_id, "upload")

def record_download(request: Request) -> None:
    """Record a download for rate limiting."""
    client_id = rate_limiter.get_client_identifier(request)
    rate_limiter.record_request(client_id, "download") 