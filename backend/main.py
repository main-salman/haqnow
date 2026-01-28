import os
import json
import dotenv
import asyncio
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse, Response
import structlog
import requests

# Load environment variables
dotenv.load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Import auth after dotenv is loaded
from app.auth.user import AuthorizedUser, AdminUser

def get_router_config() -> dict:
    """Get router configuration."""
    try:
        with open("routers.json", "r") as f:
            cfg = json.load(f)
        return cfg
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning("Could not load router configuration", error=str(e))
        return {}

def setup_cors(app: FastAPI):
    """Setup CORS middleware."""
    allowed_origins = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # Add production origins from environment
    production_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    allowed_origins.extend([origin.strip() for origin in production_origins if origin.strip()])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_security_middleware(app: FastAPI):
    """Setup security middleware."""
    # Add security headers middleware
    from app.middleware.security_headers import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Trusted host middleware
    # Allow all hosts in Kubernetes (health checks come from internal IPs)
    # Set DISABLE_HOST_CHECK=true in k8s environments
    if os.getenv("DISABLE_HOST_CHECK", "").lower() == "true":
        return  # Skip TrustedHostMiddleware in Kubernetes
    
    allowed_hosts = ["localhost", "127.0.0.1", "*.exoscale.com", "*"]
    custom_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
    allowed_hosts.extend([host.strip() for host in custom_hosts if host.strip()])
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

def setup_routers(app: FastAPI):
    """Setup API routers."""
    # Import all routers
    from app.apis.auth import router as auth_router
    from app.apis.document_processing import router as doc_router
    from app.apis.file_uploader import router as file_router
    from app.apis.search import router as search_router
    from app.apis.statistics_api import router as stats_router
    from app.apis.word_stats_api import router as word_stats_router
    from app.apis.translations import router as translations_router
    from app.apis.admin_management import router as admin_management_router
    from app.apis.rag import router as rag_router
    from app.apis.site_settings import router as site_settings_router
    from app.apis.comments import router as comments_router
    from app.apis.analytics import router as analytics_router
    from app.apis.collaborators import router as collaborators_router
    
    # Add routers with prefixes
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(doc_router, prefix="/document-processing", tags=["Document Processing"])
    app.include_router(file_router, prefix="/file-uploader", tags=["File Upload"])
    app.include_router(search_router, prefix="/search", tags=["Search"])
    app.include_router(stats_router, prefix="/statistics", tags=["Statistics"])
    app.include_router(word_stats_router, prefix="/word-stats", tags=["Word Statistics"])
    app.include_router(translations_router, prefix="/translations", tags=["Translations"])
    app.include_router(admin_management_router, prefix="/admin-management", tags=["Admin Management"])
    app.include_router(rag_router, prefix="/rag", tags=["RAG Q&A"])
    app.include_router(site_settings_router, prefix="/site-settings", tags=["Site Settings"])
    app.include_router(comments_router, prefix="/comments", tags=["Comments & Annotations"])
    app.include_router(analytics_router, prefix="/analytics", tags=["Admin Analytics"])
    app.include_router(collaborators_router, prefix="/collaborators", tags=["Collaborators"])

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="HaqNow API",
        description="Anonymous Corruption Document Exposure Platform API",
        version="1.0.0"
    )
    
    # Setup middleware
    setup_cors(app)
    setup_security_middleware(app)
    
    # Setup routers
    setup_routers(app)
    
    # Document serving route
    @app.get("/documents/{filename}")
    async def serve_document(filename: str):
        """Serve documents directly by redirecting to S3 URL."""
        try:
            from app.services.s3_service import s3_service
            
            # Construct the S3 file path
            file_path = f"documents/{filename}"
            
            # Get the public URL from S3
            file_url = s3_service.get_file_url(file_path)
            
            if not file_url:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Redirect to the S3 URL
            return RedirectResponse(url=file_url, status_code=302)
            
        except Exception as e:
            logger.error("Error serving document", filename=filename, error=str(e))
            raise HTTPException(status_code=404, detail="Document not found")
    
    # Umami Analytics Proxy - proxies tracker + API requests to avoid CORS issues.
    #
    # IMPORTANT:
    # - In production, Ingress rewrites `/api/...` -> `/<...>` (strips `/api`).
    #   So browser requests to `/api/umami/...` reach the backend as `/umami/...`.
    # - In local/dev, requests may hit the backend as `/api/umami/...` directly.
    #
    # To support both, we expose BOTH route prefixes.
    @app.api_route("/umami/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    @app.api_route("/api/umami/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def umami_proxy(path: str, request: Request):
        """Reverse-proxy Umami endpoints (e.g. script.js, /api/send) via this backend."""
        umami_url = os.getenv("UMAMI_URL", "https://analytics.haqnow.com").rstrip("/")

        # Preserve the exact path the client requested under /umami/*
        target_url = f"{umami_url}/{path.lstrip('/')}"

        try:
            body = await request.body()

            # Prepare headers (exclude hop-by-hop + host/content-length).
            excluded_request_headers = {
                "host",
                "content-length",
                "connection",
                "keep-alive",
                "proxy-authenticate",
                "proxy-authorization",
                "te",
                "trailers",
                "transfer-encoding",
                "upgrade",
            }
            headers = {
                k: v
                for k, v in request.headers.items()
                if k.lower() not in excluded_request_headers
            }

            def forward_request():
                return requests.request(
                    method=request.method,
                    url=target_url,
                    data=body if body else None,
                    headers=headers,
                    params=dict(request.query_params),
                    timeout=10,
                )

            upstream = await asyncio.to_thread(forward_request)

            excluded_response_headers = {
                "content-encoding",
                "transfer-encoding",
                "connection",
                "keep-alive",
                "proxy-authenticate",
                "proxy-authorization",
                "te",
                "trailers",
                "upgrade",
            }
            response_headers = {
                k: v
                for k, v in upstream.headers.items()
                if k.lower() not in excluded_response_headers
            }

            return Response(
                content=upstream.content,
                status_code=upstream.status_code,
                headers=response_headers,
            )
        except Exception as e:
            logger.error("Umami proxy error", path=path, error=str(e))
            # Return empty 200 to avoid breaking page loads/tracking.
            return Response(status_code=200, content=b"")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint with service status."""
        from app.services.virus_scanning_service import virus_scanning_service
        
        return {
            "status": "healthy",
            "message": "HaqNow API is running",
            "services": {
                "virus_scanning": virus_scanning_service.get_status()
            }
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "HaqNow API", "version": "1.0.0"}
    
    return app

# Create the app
app = create_app()

# Add startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("HaqNow API starting up...")
    
    # Initialize database (non-blocking)
    from app.database.database import init_db
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning("Database initialization failed, will retry on first request", error=str(e))
        # Don't raise - allow app to start even if database is temporarily unavailable
    
    # Verify essential services
    from app.services.s3_service import s3_service
    from app.services.email_service import email_service
    from app.services.virus_scanning_service import virus_scanning_service
    
    if not s3_service.client:
        logger.warning("S3 service not properly configured")
    else:
        logger.info("S3 service initialized successfully")
    
    if not email_service.client:
        logger.warning("Email service not properly configured")
    else:
        logger.info("Email service initialized successfully")
    
    if not virus_scanning_service.available:
        logger.warning("Virus scanning service not available - uploads will not be scanned")
    else:
        version = virus_scanning_service.get_virus_definitions_version()
        logger.info("Virus scanning service initialized successfully", version=version)
    
    logger.info("HaqNow API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Fadih.org API shutting down...")

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info("Starting Fadih.org API server", host=host, port=port, debug=debug)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_config=None  # Use structlog configuration
    )
