"""
Main FastAPI Application

This is the heart of the backend.
- Creates FastAPI app instance
- Configures CORS
- Sets up routes
- Handles startup/shutdown events
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

from app.core.config import settings
from app.core.database import engine, Base
from app.core.logging_config import setup_logging, get_logger
from app.api.endpoints import health, auth, documents, websocket, stores

# Setup logging first thing
setup_logging()
logger = get_logger(__name__)

# Create database tables
# In production, use Alembic migrations instead
# Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown events
    Replaces deprecated @app.on_event decorators
    """
    # Startup
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    logger.info(f"📖 API documentation: http://localhost:8000/docs")
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info(f"👋 {settings.APP_NAME} shutting down...")
    logger.info("Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Document Analyzer API",
    docs_url="/docs",  # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",  # ReDoc at http://localhost:8000/redoc
    lifespan=lifespan,
)

# Configure CORS
# Allows frontend (running on port 5173) to call backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests and their response times
    """
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"➡️  {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(
        f"⬅️  {request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Duration: {duration:.3f}s"
    )
    
    return response


# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_PREFIX}/documents",
    tags=["Documents"]
)
app.include_router(
    stores.router,
    prefix=f"{settings.API_V1_PREFIX}/stores",
    tags=["Stores"]
)
app.include_router(
    websocket.router,
    tags=["WebSocket"]
)


@app.get("/")
async def root():
    """
    Root endpoint
    Quick check that API is running
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
