import os
import json
import dotenv
from fastapi import FastAPI, APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import RedirectResponse
import structlog

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
    # Trusted host middleware
    allowed_hosts = ["localhost", "127.0.0.1", "*.exoscale.com"]
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
    # from app.apis.translations import router as translations_router
    
    # Add routers with prefixes
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(doc_router, prefix="/document-processing", tags=["Document Processing"])
    app.include_router(file_router, prefix="/file-uploader", tags=["File Upload"])
    app.include_router(search_router, prefix="/search", tags=["Search"])
    app.include_router(stats_router, prefix="/statistics", tags=["Statistics"])
    app.include_router(word_stats_router, prefix="/word-stats", tags=["Word Statistics"])
    # app.include_router(translations_router, prefix="/translations", tags=["Translations"])

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Fadih.org API",
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
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "message": "Fadih.org API is running"}
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Fadih.org API", "version": "1.0.0"}
    
    return app

# Create the app
app = create_app()

# Add startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Fadih.org API starting up...")
    
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
    
    if not s3_service.client:
        logger.warning("S3 service not properly configured")
    else:
        logger.info("S3 service initialized successfully")
    
    if not email_service.client:
        logger.warning("Email service not properly configured")
    else:
        logger.info("Email service initialized successfully")
    
    logger.info("Fadih.org API startup complete")

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
