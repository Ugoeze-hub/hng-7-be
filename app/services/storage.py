import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from app.config import get_settings

class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.settings.s3_endpoint,
            aws_access_key_id=self.settings.aws_access_key,
            aws_secret_access_key=self.settings.aws_secret_key
        )
        self.bucket = self.settings.s3_bucket
    
    def initialize_bucket(self):
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket)
            except Exception as e:
                print(f"Warning: Could not create S3 bucket: {e}")
    
    def upload_file(self, file_content: bytes, key: str) -> str:
        """Upload file to S3/MinIO."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_content
            )
            return key
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload to S3: {str(e)}"
            )
    
    def delete_file(self, key: str) -> bool:
        """Delete file from S3/MinIO."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            print(f"Warning: Could not delete from S3: {e}")
            return False
    
    def get_file(self, key: str) -> bytes:
        """Retrieve file from S3/MinIO."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {str(e)}"
            )