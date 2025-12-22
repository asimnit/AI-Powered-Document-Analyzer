"""
Test S3 Connection

Quick script to verify AWS S3 credentials and bucket access.
Run this before using the storage service in production.
"""

import sys
import boto3
from botocore.exceptions import ClientError

# Add app to path for imports
sys.path.insert(0, '.')

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def test_s3_connection():
    """Test S3 connection and permissions"""
    
    logger.info("🧪 Testing S3 connection...")
    logger.info(f"📦 Bucket: {settings.S3_BUCKET_NAME}")
    logger.info(f"🌍 Region: {settings.AWS_REGION}")
    logger.info(f"🔑 Access Key: {settings.AWS_ACCESS_KEY_ID[:8]}...")
    
    try:
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Test 1: List objects (tests bucket access and permissions)
        logger.info("\n📋 Test 1: Listing bucket objects...")
        response = s3.list_objects_v2(
            Bucket=settings.S3_BUCKET_NAME,
            MaxKeys=10
        )
        
        object_count = response.get('KeyCount', 0)
        logger.info(f"✅ Success! Found {object_count} objects in bucket")
        
        # Test 2: Check bucket location
        logger.info("\n📍 Test 2: Getting bucket location...")
        location = s3.get_bucket_location(Bucket=settings.S3_BUCKET_NAME)
        bucket_region = location['LocationConstraint'] or 'us-east-1'
        logger.info(f"✅ Bucket region: {bucket_region}")
        
        if bucket_region != settings.AWS_REGION:
            logger.warning(f"⚠️  Bucket region ({bucket_region}) differs from configured region ({settings.AWS_REGION})")
        
        # Test 3: Test upload permission with a tiny test file
        logger.info("\n📤 Test 3: Testing upload permission...")
        test_key = "_test_connection.txt"
        test_content = b"S3 connection test successful!"
        
        s3.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=test_key,
            Body=test_content
        )
        logger.info(f"✅ Upload successful: {test_key}")
        
        # Test 4: Test download permission
        logger.info("\n📥 Test 4: Testing download permission...")
        obj = s3.get_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=test_key
        )
        content = obj['Body'].read()
        logger.info(f"✅ Download successful: {len(content)} bytes")
        
        # Test 5: Test delete permission
        logger.info("\n🗑️  Test 5: Testing delete permission...")
        s3.delete_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=test_key
        )
        logger.info(f"✅ Delete successful")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("="*60)
        logger.info("✅ S3 connection is working correctly")
        logger.info("✅ All required permissions are in place")
        logger.info("✅ Ready to use storage service")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        
        logger.error("\n" + "="*60)
        logger.error("❌ S3 CONNECTION FAILED")
        logger.error("="*60)
        logger.error(f"Error Code: {error_code}")
        logger.error(f"Error Message: {error_msg}")
        
        # Provide helpful hints based on error
        if error_code == 'NoSuchBucket':
            logger.error("\n💡 Hint: The bucket does not exist")
            logger.error("   - Check bucket name spelling")
            logger.error("   - Verify bucket was created in AWS Console")
            logger.error(f"   - Current bucket name: {settings.S3_BUCKET_NAME}")
            
        elif error_code == 'InvalidAccessKeyId':
            logger.error("\n💡 Hint: Invalid AWS Access Key ID")
            logger.error("   - Check AWS_ACCESS_KEY_ID in .env file")
            logger.error("   - Verify credentials in AWS IAM Console")
            
        elif error_code == 'SignatureDoesNotMatch':
            logger.error("\n💡 Hint: Invalid AWS Secret Access Key")
            logger.error("   - Check AWS_SECRET_ACCESS_KEY in .env file")
            logger.error("   - Make sure there are no extra spaces")
            
        elif error_code == 'AccessDenied':
            logger.error("\n💡 Hint: Permission denied")
            logger.error("   - Check IAM user permissions")
            logger.error("   - User needs: s3:ListBucket, s3:GetObject, s3:PutObject, s3:DeleteObject")
            
        else:
            logger.error("\n💡 Check AWS Console for more details")
        
        return False
        
    except Exception as e:
        logger.error("\n" + "="*60)
        logger.error("❌ UNEXPECTED ERROR")
        logger.error("="*60)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AWS S3 CONNECTION TEST")
    print("="*60 + "\n")
    
    success = test_s3_connection()
    
    if success:
        print("\n✅ You're ready to start uploading documents!")
        sys.exit(0)
    else:
        print("\n❌ Please fix the issues above and try again.")
        sys.exit(1)
