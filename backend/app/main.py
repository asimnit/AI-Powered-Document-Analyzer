"""
Main FastAPI Application

This is the heart of the backend.
- Creates FastAPI app instance
- Configures CORS
- Sets up routes
- Handles startup/shutdown events
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import health, auth

# Create database tables
# In production, use Alembic migrations instead
# Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Document Analyzer API",
    docs_url="/docs",  # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",  # ReDoc at http://localhost:8000/redoc
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

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)


@app.on_event("startup")
async def startup_event():
    """
    Runs when server starts
    Good place for initialization logic
    """
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started!")
    print(f"📖 API documentation: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Runs when server stops
    Good place for cleanup logic
    """
    print(f"👋 {settings.APP_NAME} shutting down...")


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
