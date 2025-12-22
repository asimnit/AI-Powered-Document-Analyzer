"""
Storage Service

Handles file storage operations with support for both:
- AWS S3 (production)
- Local filesystem (development)

Provides abstraction layer to switch between storage backends.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class StorageService:
    """
    File storage abstraction layer
    
    Supports both S3 and local filesystem storage.
    Automatically selects backend based on S3_UPLOAD_ENABLED setting.
    """
    
    def __init__(self):
        """Initialize storage service with appropriate backend"""
        self.use_s3 = settings.S3_UPLOAD_ENABLED
        
        if self.use_s3:
            logger.info("📦 Initializing S3 storage")
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket_name = settings.S3_BUCKET_NAME
        else:
            logger.info("📁 Using local filesystem storage")
            self.upload_dir = Path(settings.UPLOAD_DIR)
            self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_unique_filename(self, original_filename: str, user_id: int) -> str:
        """
        Generate unique filename to prevent collisions
        
        Format: {user_id}/{timestamp}_{uuid}_{original_filename}
        Example: 123/20251222_abc123_document.pdf
        
        Args:
            original_filename: Original uploaded filename
            user_id: User ID for organizing files
            
        Returns:
            Unique file path/key
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = "".join(c for c in original_filename if c.isalnum() or c in "._- ")
        
        return f"{user_id}/{timestamp}_{unique_id}_{safe_filename}"
    
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        user_id: int,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to storage
        
        Args:
            file: File object or bytes
            filename: Original filename
            user_id: User ID for organizing files
            content_type: MIME type (optional)
            
        Returns:
            File path/key in storage
            
        Raises:
            Exception: If upload fails
        """
        file_path = self.generate_unique_filename(filename, user_id)
        
        try:
            if self.use_s3:
                # Upload to S3
                extra_args = {}
                if content_type:
                    extra_args['ContentType'] = content_type
                
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    file_path,
                    ExtraArgs=extra_args
                )
                logger.info(f"✅ Uploaded to S3: {file_path}")
            else:
                # Save to local filesystem
                local_path = self.upload_dir / file_path
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(local_path, 'wb') as f:
                    f.write(file.read())
                
                logger.info(f"✅ Saved locally: {file_path}")
            
            return file_path
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from storage
        
        Args:
            file_path: Path/key of file in storage
            
        Returns:
            File content as bytes
            
        Raises:
            Exception: If download fails
        """
        try:
            if self.use_s3:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                content = response['Body'].read()
                logger.info(f"✅ Downloaded from S3: {file_path}")
            else:
                local_path = self.upload_dir / file_path
                with open(local_path, 'rb') as f:
                    content = f.read()
                logger.info(f"✅ Read from local: {file_path}")
            
            return content
            
        except ClientError as e:
            logger.error(f"❌ S3 download failed: {e}")
            raise Exception(f"Failed to download file from S3: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage
        
        Args:
            file_path: Path/key of file in storage
            
        Returns:
            True if deletion successful
            
        Raises:
            Exception: If deletion fails
        """
        try:
            if self.use_s3:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                logger.info(f"🗑️  Deleted from S3: {file_path}")
            else:
                local_path = self.upload_dir / file_path
                if local_path.exists():
                    local_path.unlink()
                logger.info(f"🗑️  Deleted from local: {file_path}")
            
            return True
            
        except ClientError as e:
            logger.error(f"❌ S3 deletion failed: {e}")
            raise Exception(f"Failed to delete file from S3: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Deletion failed: {e}")
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage
        
        Args:
            file_path: Path/key of file in storage
            
        Returns:
            True if file exists
        """
        try:
            if self.use_s3:
                self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                return True
            else:
                local_path = self.upload_dir / file_path
                return local_path.exists()
        except ClientError:
            return False
        except Exception:
            return False
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Generate pre-signed URL for file access
        
        Args:
            file_path: Path/key of file in storage
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Pre-signed URL for S3 or local file path
        """
        try:
            if self.use_s3:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': file_path
                    },
                    ExpiresIn=expires_in
                )
                logger.info(f"🔗 Generated pre-signed URL for: {file_path}")
                return url
            else:
                # For local files, return relative path
                return f"/api/v1/documents/download/{file_path}"
        except ClientError as e:
            logger.error(f"❌ Failed to generate URL: {e}")
            raise Exception(f"Failed to generate file URL: {str(e)}")


# Create singleton instance
storage_service = StorageService()
