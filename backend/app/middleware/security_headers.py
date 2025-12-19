"""Security headers middleware for FastAPI backend."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.
    
    These headers provide protection against common web vulnerabilities:
    - XSS attacks
    - Clickjacking
    - MIME type sniffing
    - Information leakage
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Prevent XSS attacks by blocking pages from loading when reflected XSS detected
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking by controlling iframe embedding
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # Control referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), "
            "usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
        )
        
        # Enforce HTTPS - max-age is 1 year (31536000 seconds)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        
        # Cross-origin isolation policies
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # Prevent Adobe Flash and PDF from making cross-domain requests
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # Remove server information to reduce information leakage
        response.headers["Server"] = "HaqNow"
        
        # Cache control for API responses (no sensitive data should be cached)
        if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
            if "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
                response.headers["Pragma"] = "no-cache"
        
        return response














