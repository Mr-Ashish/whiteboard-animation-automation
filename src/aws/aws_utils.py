"""AWS S3 upload utilities"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Colored logging for differentiation
from ..utils.log_utils import log_success

# Load environment variables from .env file
load_dotenv()


def upload_to_s3(file_path, custom_name=None):
    """Upload file to AWS S3 and return public URL

    Args:
        file_path: Path to the file to upload
        custom_name: Optional custom name for the uploaded file

    Returns:
        str: Public URL of the uploaded file

    Raises:
        ValueError: If AWS credentials are not configured
        ImportError: If boto3 is not installed
    """
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        raise ImportError(
            "boto3 is required for S3 uploads. Install it with:\n"
            "  pip install boto3"
        )

    # Get AWS credentials from environment
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('AWS_S3_BUCKET')
    region = os.getenv('AWS_REGION', 'us-east-1')
    s3_prefix = os.getenv('AWS_S3_PREFIX', '')

    # Validate credentials
    if not access_key or not secret_key:
        raise ValueError(
            "AWS credentials not found. Please set them in .env file:\n"
            "  AWS_ACCESS_KEY_ID=your_access_key\n"
            "  AWS_SECRET_ACCESS_KEY=your_secret_key\n"
            "\nCopy .env.example to .env and add your credentials."
        )

    if not bucket_name:
        raise ValueError(
            "AWS S3 bucket not configured. Please set in .env file:\n"
            "  AWS_S3_BUCKET=your-bucket-name"
        )

    file_path = Path(file_path)
    if not file_path.exists():
        raise ValueError(f"File not found: {file_path}")

    # Determine S3 object name
    if custom_name:
        object_name = custom_name
    else:
        object_name = file_path.name

    # Add prefix if configured
    if s3_prefix:
        object_name = f"{s3_prefix.rstrip('/')}/{object_name}"

    print(f"\nUploading to S3...")
    print(f"  Bucket: {bucket_name}")
    print(f"  File: {object_name}")

    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

        # Upload file
        s3_client.upload_file(
            str(file_path),
            bucket_name,
            object_name,
            ExtraArgs={'ContentType': 'video/mp4'}
        )

        # Generate public URL
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_name}"

        log_success(f"✓ Upload successful!")
        print(f"  Public URL: {url}")

        return url

    except NoCredentialsError:
        raise ValueError("Invalid AWS credentials")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            raise ValueError(f"S3 bucket '{bucket_name}' does not exist")
        else:
            raise ValueError(f"S3 upload failed: {e}")


def check_aws_credentials():
    """Check if AWS credentials are configured

    Returns:
        bool: True if credentials are configured, False otherwise
    """
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('AWS_S3_BUCKET')

    return bool(access_key and secret_key and bucket_name)


def get_aws_config_status():
    """Get AWS configuration status for display

    Returns:
        dict: Configuration status information
    """
    return {
        'access_key_set': bool(os.getenv('AWS_ACCESS_KEY_ID')),
        'secret_key_set': bool(os.getenv('AWS_SECRET_ACCESS_KEY')),
        'bucket_set': bool(os.getenv('AWS_S3_BUCKET')),
        'bucket_name': os.getenv('AWS_S3_BUCKET', 'Not configured'),
        'region': os.getenv('AWS_REGION', 'us-east-1'),
        'prefix': os.getenv('AWS_S3_PREFIX', 'None'),
    }
