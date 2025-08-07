"""S3 service for file storage using Exoscale S3 bucket."""

import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import structlog
from uuid import uuid4
import mimetypes
from urllib.parse import quote

logger = structlog.get_logger()

class S3Service:
    """S3 service for file storage."""
    
    def __init__(self):
        self.access_key = os.getenv("EXOSCALE_S3_ACCESS_KEY")
        self.secret_key = os.getenv("EXOSCALE_S3_SECRET_KEY")
        self.endpoint_url = f"https://{os.getenv('EXOSCALE_S3_ENDPOINT')}"
        self.region = os.getenv("EXOSCALE_S3_REGION")
        self.bucket_name = os.getenv("EXOSCALE_BUCKET")
        self.public_url_base = os.getenv("EXOSCALE_S3_PUBLIC_URL")
        
        self.client = None
        
        if all([self.access_key, self.secret_key, self.endpoint_url, self.bucket_name]):
            try:
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    endpoint_url=self.endpoint_url,
                    region_name=self.region
                )
                logger.info("S3 client initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize S3 client", error=str(e))
        else:
            logger.error("S3 configuration incomplete")
    
    def upload_file(self, file_content: BinaryIO, file_name: str, content_type: str = None) -> Optional[str]:
        """Upload file to S3 bucket and return the file path."""
        if not self.client:
            logger.error("S3 client not initialized")
            return None
        
        try:
            # Generate unique file path
            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{uuid4()}{file_extension}"
            file_path = f"documents/{unique_filename}"
            
            # Determine content type
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = "application/octet-stream"
            
            # Upload file
            self.client.upload_fileobj(
                file_content,
                self.bucket_name,
                file_path,
                ExtraArgs={
                    'ContentType': content_type,
                    'ACL': 'public-read'  # Make file publicly accessible
                }
            )
            
            logger.info("File uploaded successfully", 
                       file_path=file_path, 
                       content_type=content_type)
            return file_path
            
        except ClientError as e:
            logger.error("Failed to upload file to S3", 
                        file_name=file_name, 
                        error=str(e))
            return None
    
    def get_file_url(self, file_path: str) -> str:
        """Get public URL for a file."""
        if self.public_url_base:
            return f"{self.public_url_base}/{file_path}"
        return f"{self.endpoint_url}/{self.bucket_name}/{file_path}"
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from S3 bucket."""
        if not self.client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=file_path)
            logger.info("File deleted successfully", file_path=file_path)
            return True
            
        except ClientError as e:
            logger.error("Failed to delete file from S3", 
                        file_path=file_path, 
                        error=str(e))
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3 bucket."""
        if not self.client:
            return False
        
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError:
            return False
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size in bytes."""
        if not self.client:
            return None
        
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=file_path)
            return response['ContentLength']
        except ClientError as e:
            logger.error("Failed to get file size", 
                        file_path=file_path, 
                        error=str(e))
            return None
    
    def get_download_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a presigned URL for downloading a file."""
        if not self.client:
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_path},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error("Failed to generate presigned URL", 
                        file_path=file_path, 
                        error=str(e))
            return None

# Global S3 service instance
s3_service = S3Service() 