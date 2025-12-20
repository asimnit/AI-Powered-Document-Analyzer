"""
Health Check Endpoint

Simple endpoint to check if the API is running.
Useful for monitoring and debugging.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Simple JSON response confirming API is alive
    """
    return {
        "status": "healthy",
        "message": "API is running"
    }
