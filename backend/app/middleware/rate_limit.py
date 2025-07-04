"""Rate limiting middleware for document uploads."""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis
import os

# Redis configuration for rate limiting
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
UPLOAD_TIMEOUT_SECONDS = int(os.getenv("UPLOAD_TIMEOUT_SECONDS", "120"))  # 2 minutes

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
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def check_rate_limit(self, ip: str, endpoint: str = "upload") -> Optional[float]:
        """Check if IP is rate limited. Returns remaining time if limited, None if allowed."""
        key = f"rate_limit:{endpoint}:{ip}"
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
                return self._check_memory_rate_limit(ip, endpoint, current_time)
        else:
            return self._check_memory_rate_limit(ip, endpoint, current_time)
    
    def _check_memory_rate_limit(self, ip: str, endpoint: str, current_time: float) -> Optional[float]:
        """Check rate limit using in-memory store."""
        key = f"{endpoint}:{ip}"
        if key in _memory_store:
            last_upload_time = _memory_store[key]
            time_passed = current_time - last_upload_time
            if time_passed < UPLOAD_TIMEOUT_SECONDS:
                return UPLOAD_TIMEOUT_SECONDS - time_passed
        return None
    
    def record_request(self, ip: str, endpoint: str = "upload") -> None:
        """Record a request timestamp for rate limiting."""
        key = f"rate_limit:{endpoint}:{ip}"
        current_time = time.time()
        
        if self.redis_client:
            try:
                self.redis_client.setex(key, UPLOAD_TIMEOUT_SECONDS, current_time)
                return
            except Exception as e:
                print(f"Redis error: {e}")
        
        # Fall back to memory store
        memory_key = f"{endpoint}:{ip}"
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
    ip = rate_limiter.get_client_ip(request)
    remaining_time = rate_limiter.check_rate_limit(ip, "upload")
    
    if remaining_time is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Upload rate limit exceeded. Please wait before uploading another document.",
                "remaining_time": int(remaining_time),
                "timeout_seconds": UPLOAD_TIMEOUT_SECONDS
            }
        )

def check_download_rate_limit(request: Request) -> None:
    """Check if download is rate limited and raise HTTPException if so."""
    ip = rate_limiter.get_client_ip(request)
    remaining_time = rate_limiter.check_rate_limit(ip, "download")
    
    if remaining_time is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Download rate limit exceeded. Please wait before downloading another document.",
                "remaining_time": int(remaining_time),
                "timeout_seconds": UPLOAD_TIMEOUT_SECONDS
            }
        )

def record_upload(request: Request) -> None:
    """Record an upload for rate limiting."""
    ip = rate_limiter.get_client_ip(request)
    rate_limiter.record_request(ip, "upload")

def record_download(request: Request) -> None:
    """Record a download for rate limiting."""
    ip = rate_limiter.get_client_ip(request)
    rate_limiter.record_request(ip, "download") 