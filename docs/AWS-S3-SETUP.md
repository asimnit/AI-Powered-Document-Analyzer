# AWS S3 Setup Guide

## 📦 AWS S3 Configuration

This document explains how to set up AWS S3 for the AI-Powered Document Analyzer.

---

## Prerequisites

- AWS Account
- AWS CLI installed (optional but recommended)
- Basic understanding of AWS IAM

---

## Step 1: Create S3 Bucket

1. **Go to AWS Console** → S3 Service
2. **Click "Create bucket"**
3. **Bucket Settings:**
   - **Bucket name**: `your-document-analyzer-bucket` (must be globally unique)
   - **AWS Region**: Choose closest to your users (e.g., `us-east-1`)
   - **Block Public Access**: Keep **all public access blocked** ✅
   - **Bucket Versioning**: Enable (recommended)
   - **Encryption**: Enable with SSE-S3 or SSE-KMS
4. **Click "Create bucket"**

---

## Step 2: Create IAM User

1. **Go to AWS Console** → IAM Service → Users
2. **Click "Add users"**
3. **User Settings:**
   - **User name**: `doc-analyzer-app`
   - **Access type**: ✅ Programmatic access
4. **Click "Next: Permissions"**

---

## Step 3: Set IAM Permissions

**Option A: Use Managed Policy (Quick)**
1. Attach existing policy: `AmazonS3FullAccess`
   - ⚠️ Only for development. Too permissive for production.

**Option B: Create Custom Policy (Recommended for Production)**
1. Click "Attach policies directly" → "Create policy"
2. Use this JSON policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DocumentAnalyzerS3Access",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-document-analyzer-bucket",
                "arn:aws:s3:::your-document-analyzer-bucket/*"
            ]
        }
    ]
}
```

3. **Policy name**: `DocumentAnalyzerS3Policy`
4. Attach this policy to your user

---

## Step 4: Get Access Keys

1. After creating user, you'll see:
   - **Access key ID**: `AKIAIOSFODNN7EXAMPLE`
   - **Secret access key**: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
2. **⚠️ IMPORTANT**: Download and save these credentials securely!
3. You can only view the secret key **once** during creation

---

## Step 5: Update Backend Configuration

### Update `.env` file:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-document-analyzer-bucket
S3_UPLOAD_ENABLED=True
```

### For Local Development (No S3):
```bash
S3_UPLOAD_ENABLED=False
```

---

## Step 6: Install Dependencies

```bash
cd backend
pip install boto3 botocore
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

---

## Step 7: Test S3 Connection

Create a test script: `backend/test_s3.py`

```python
import boto3
from app.core.config import settings

def test_s3_connection():
    """Test S3 connection and permissions"""
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Test bucket access
        response = s3.list_objects_v2(
            Bucket=settings.S3_BUCKET_NAME,
            MaxKeys=1
        )
        
        print("✅ S3 connection successful!")
        print(f"📦 Bucket: {settings.S3_BUCKET_NAME}")
        print(f"🌍 Region: {settings.AWS_REGION}")
        return True
        
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

if __name__ == "__main__":
    test_s3_connection()
```

Run test:
```bash
python test_s3.py
```

---

## Security Best Practices

### ✅ DO:
- Use IAM users with minimal required permissions
- Enable bucket versioning
- Enable server-side encryption
- Use environment variables for credentials
- Rotate access keys regularly
- Enable CloudTrail logging
- Set up bucket lifecycle policies

### ❌ DON'T:
- Never commit `.env` file to Git
- Never use root AWS account credentials
- Never make S3 bucket public
- Never hardcode credentials in code
- Never give `s3:*` permissions

---

## CORS Configuration (if using direct uploads)

If you plan to upload directly from browser to S3:

1. Go to S3 bucket → Permissions → CORS
2. Add this configuration:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": [
            "http://localhost:5173",
            "https://your-production-domain.com"
        ],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

---

## Cost Estimation

### S3 Pricing (us-east-1):
- **Storage**: $0.023 per GB/month
- **PUT requests**: $0.005 per 1,000 requests
- **GET requests**: $0.0004 per 1,000 requests
- **Data transfer out**: $0.09 per GB (first 10TB)

### Example Monthly Costs:
- **10 GB storage**: ~$0.23
- **1,000 uploads**: ~$0.005
- **10,000 downloads**: ~$0.004
- **1 GB transfer**: ~$0.09
- **Total**: ~$0.33/month

---

## Bucket Lifecycle Policy (Cost Optimization)

To automatically delete old files:

```json
{
    "Rules": [
        {
            "Id": "DeleteOldDocuments",
            "Status": "Enabled",
            "Expiration": {
                "Days": 90
            },
            "Filter": {
                "Prefix": ""
            }
        }
    ]
}
```

---

## Monitoring

### CloudWatch Metrics to Watch:
- `BucketSizeBytes` - Storage usage
- `NumberOfObjects` - Object count
- `AllRequests` - Request volume
- `4xxErrors` - Client errors
- `5xxErrors` - Server errors

### Set up Alarms:
- Alert when storage > X GB
- Alert on high error rates
- Alert on unusual request patterns

---

## Troubleshooting

### Error: "Access Denied"
- Check IAM permissions
- Verify bucket name is correct
- Ensure credentials are valid

### Error: "Bucket does not exist"
- Check bucket name spelling
- Verify region is correct
- Check if bucket was created

### Error: "Invalid credentials"
- Verify AWS_ACCESS_KEY_ID
- Verify AWS_SECRET_ACCESS_KEY
- Check if keys are active in IAM

### Slow uploads
- Check internet connection
- Consider using multipart upload for large files
- Check AWS region latency

---

## Production Checklist

- [ ] S3 bucket created with unique name
- [ ] IAM user created with minimal permissions
- [ ] Access keys generated and saved securely
- [ ] `.env` file updated with real credentials
- [ ] `.env` added to `.gitignore`
- [ ] Bucket encryption enabled
- [ ] Bucket versioning enabled
- [ ] CORS configured (if needed)
- [ ] Lifecycle policies set up
- [ ] CloudWatch alarms configured
- [ ] S3 connection tested successfully
- [ ] Backup strategy defined

---

## Additional Resources

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)

---

## Need Help?

Common issues and solutions are documented in the troubleshooting section above. For AWS-specific issues, check:
- AWS Console → CloudTrail for audit logs
- AWS Console → CloudWatch for metrics
- S3 bucket access logs (if enabled)
