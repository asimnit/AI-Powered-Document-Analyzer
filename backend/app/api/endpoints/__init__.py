"""
Endpoints Package

Exports all API route modules
"""

from app.api.endpoints import health, auth, documents

__all__ = ["health", "auth", "documents"]
