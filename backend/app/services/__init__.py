"""
Storage Service Package

Exports storage service for use in other modules
"""

from app.services.storage import storage_service, StorageService

__all__ = ["storage_service", "StorageService"]
