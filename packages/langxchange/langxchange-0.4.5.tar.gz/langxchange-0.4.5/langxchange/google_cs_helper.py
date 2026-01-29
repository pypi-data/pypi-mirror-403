"""
Enhanced Google Cloud Storage Helper

An improved, production-ready Google Cloud Storage helper class with comprehensive
error handling, type hints, logging, and additional utility methods.

Author: Langxchange
Date: 2025-07-11
"""

import os
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
import json
from google.cloud import storage
from google.oauth2 import service_account
from google.api_core import exceptions as gcs_exceptions


class EnhancedGoogleCloudStorageHelper:
    """
    Enhanced Google Cloud Storage helper class providing comprehensive GCS operations
    with robust error handling, logging, and utility methods.
    """
    
    def __init__(
        self, 
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the GCS helper with credentials and configuration.
        
        Args:
            credentials_path: Path to service account JSON file
            project_id: GCP project ID (overrides environment variable)
            logger: Custom logger instance
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.logger = logger or self._setup_logger()
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be provided via parameter or environment variable")
        
        self.client = self._initialize_client(credentials_path)
        self.logger.info(f"GCS Helper initialized for project: {self.project_id}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger for the class."""
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _initialize_client(self, credentials_path: Optional[str]) -> storage.Client:
        """Initialize the GCS client with appropriate credentials."""
        credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        try:
            if credentials_path and os.path.isfile(credentials_path):
                self.logger.info(f"Using service account credentials from: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                return storage.Client(project=self.project_id, credentials=credentials)
            else:
                self.logger.info("Using Application Default Credentials (ADC)")
                return storage.Client(project=self.project_id)
        except Exception as e:
            raise RuntimeError(f"Failed to initialize GCS client: {e}")
    
    def _validate_bucket_name(self, bucket_name: str) -> None:
        """Validate bucket name according to GCS naming rules."""
        if not bucket_name:
            raise ValueError("Bucket name cannot be empty")
        
        if len(bucket_name) < 3 or len(bucket_name) > 63:
            raise ValueError("Bucket name must be between 3 and 63 characters")
        
        if not bucket_name.replace('-', '').replace('_', '').replace('.', '').isalnum():
            raise ValueError("Bucket name can only contain lowercase letters, numbers, hyphens, and underscores")
    
    def _validate_file_path(self, file_path: str) -> None:
        """Validate that file path exists and is accessible."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")
    
    def bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if a bucket exists.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            True if bucket exists, False otherwise
        """
        try:
            self._validate_bucket_name(bucket_name)
            bucket = self.client.bucket(bucket_name)
            return bucket.exists()
        except gcs_exceptions.NotFound:
            return False
        except Exception as e:
            self.logger.error(f"Error checking bucket existence: {e}")
            return False
    
    def create_bucket(
        self, 
        bucket_name: str, 
        location: str = "US",
        storage_class: str = "STANDARD",
        force_create: bool = False
    ) -> storage.Bucket:
        """
        Create a new bucket with enhanced configuration options.
        
        Args:
            bucket_name: Name of the bucket to create
            location: Bucket location (default: "US")
            storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
            force_create: If True, don't check if bucket already exists
            
        Returns:
            Created or existing bucket object
            
        Raises:
            RuntimeError: If bucket creation fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            
            bucket = self.client.bucket(bucket_name)
            
            if not force_create and bucket.exists():
                self.logger.info(f"Bucket {bucket_name} already exists")
                return bucket
            
            bucket = self.client.create_bucket(
                bucket_name,
                location=location
            )
            bucket.storage_class = storage_class
            bucket.patch()
            
            self.logger.info(f"Successfully created bucket: {bucket_name} in {location}")
            return bucket
            
        except gcs_exceptions.Conflict:
            self.logger.warning(f"Bucket {bucket_name} already exists")
            return self.client.bucket(bucket_name)
        except Exception as e:
            error_msg = f"Failed to create bucket {bucket_name}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def upload_file(
        self, 
        bucket_name: str, 
        file_path: str, 
        destination_blob_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to GCS bucket with enhanced options.
        
        Args:
            bucket_name: Target bucket name
            file_path: Local file path to upload
            destination_blob_name: Remote blob name (defaults to filename)
            metadata: Custom metadata for the blob
            content_type: MIME type of the file
            
        Returns:
            Dictionary with upload information
            
        Raises:
            RuntimeError: If upload fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            self._validate_file_path(file_path)
            
            if not destination_blob_name:
                destination_blob_name = os.path.basename(file_path)
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            
            # Set metadata if provided
            if metadata:
                blob.metadata = metadata
            
            # Set content type if provided
            if content_type:
                blob.content_type = content_type
            
            # Upload file
            blob.upload_from_filename(file_path)
            
            upload_info = {
                "bucket": bucket_name,
                "blob_name": destination_blob_name,
                "size": blob.size,
                "md5_hash": blob.md5_hash,
                "etag": blob.etag,
                "public_url": f"gs://{bucket_name}/{destination_blob_name}",
                "upload_time": blob.time_created
            }
            
            self.logger.info(f"Successfully uploaded {file_path} to gs://{bucket_name}/{destination_blob_name}")
            return upload_info
            
        except Exception as e:
            error_msg = f"Failed to upload file {file_path}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def download_file(
        self, 
        bucket_name: str, 
        blob_name: str, 
        destination_file_path: str,
        create_dirs: bool = True
    ) -> Dict[str, Any]:
        """
        Download a file from GCS bucket.
        
        Args:
            bucket_name: Source bucket name
            blob_name: Remote blob name
            destination_file_path: Local destination path
            create_dirs: Create parent directories if they don't exist
            
        Returns:
            Dictionary with download information
            
        Raises:
            RuntimeError: If download fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            if not blob.exists():
                raise FileNotFoundError(f"Blob {blob_name} not found in bucket {bucket_name}")
            
            if create_dirs:
                Path(destination_file_path).parent.mkdir(parents=True, exist_ok=True)
            
            blob.download_to_filename(destination_file_path)
            
            download_info = {
                "bucket": bucket_name,
                "blob_name": blob_name,
                "local_path": destination_file_path,
                "size": blob.size,
                "md5_hash": blob.md5_hash,
                "content_type": blob.content_type,
                "download_time": blob.updated
            }
            
            self.logger.info(f"Successfully downloaded gs://{bucket_name}/{blob_name} to {destination_file_path}")
            return download_info
            
        except Exception as e:
            error_msg = f"Failed to download blob {blob_name}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def list_blobs(
        self, 
        bucket_name: str, 
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
        include_metadata: bool = False
    ) -> List[Union[str, Dict[str, Any]]]:
        """
        List blobs in a bucket with enhanced filtering options.
        
        Args:
            bucket_name: Bucket name to list
            prefix: Filter blobs by prefix
            delimiter: Group blobs by delimiter (e.g., '/' for folder-like structure)
            include_metadata: Return blob metadata along with names
            
        Returns:
            List of blob names or blob information dictionaries
            
        Raises:
            RuntimeError: If listing fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            
            blobs = self.client.list_blobs(
                bucket_name, 
                prefix=prefix,
                delimiter=delimiter
            )
            
            if include_metadata:
                result = []
                for blob in blobs:
                    blob_info = {
                        "name": blob.name,
                        "size": blob.size,
                        "content_type": blob.content_type,
                        "md5_hash": blob.md5_hash,
                        "etag": blob.etag,
                        "time_created": blob.time_created,
                        "updated": blob.updated,
                        "metadata": blob.metadata or {}
                    }
                    result.append(blob_info)
                return result
            else:
                return [blob.name for blob in blobs]
                
        except Exception as e:
            error_msg = f"Failed to list blobs in bucket {bucket_name}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def delete_blob(self, bucket_name: str, blob_name: str) -> bool:
        """
        Delete a blob from the bucket.
        
        Args:
            bucket_name: Bucket name
            blob_name: Blob name to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            RuntimeError: If deletion fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            if not blob.exists():
                self.logger.warning(f"Blob {blob_name} does not exist in bucket {bucket_name}")
                return False
            
            blob.delete()
            self.logger.info(f"Successfully deleted blob: gs://{bucket_name}/{blob_name}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete blob {blob_name}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete a bucket (must be empty unless force=True).
        
        Args:
            bucket_name: Bucket name to delete
            force: If True, delete all blobs in bucket first
            
        Returns:
            True if deletion was successful
            
        Raises:
            RuntimeError: If deletion fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            
            bucket = self.client.bucket(bucket_name)
            
            if not bucket.exists():
                self.logger.warning(f"Bucket {bucket_name} does not exist")
                return False
            
            if force:
                # Delete all blobs first
                blobs = list(bucket.list_blobs())
                for blob in blobs:
                    blob.delete()
                self.logger.info(f"Deleted {len(blobs)} blobs from bucket {bucket_name}")
            
            bucket.delete()
            self.logger.info(f"Successfully deleted bucket: {bucket_name}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete bucket {bucket_name}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def copy_blob(
        self, 
        source_bucket: str, 
        source_blob: str, 
        destination_bucket: str, 
        destination_blob: str
    ) -> Dict[str, Any]:
        """
        Copy a blob from one location to another.
        
        Args:
            source_bucket: Source bucket name
            source_blob: Source blob name
            destination_bucket: Destination bucket name
            destination_blob: Destination blob name
            
        Returns:
            Dictionary with copy operation information
            
        Raises:
            RuntimeError: If copy operation fails
        """
        try:
            self._validate_bucket_name(source_bucket)
            self._validate_bucket_name(destination_bucket)
            
            source_bucket_obj = self.client.bucket(source_bucket)
            source_blob_obj = source_bucket_obj.blob(source_blob)
            
            if not source_blob_obj.exists():
                raise FileNotFoundError(f"Source blob {source_blob} not found in bucket {source_bucket}")
            
            destination_bucket_obj = self.client.bucket(destination_bucket)
            
            # Perform the copy
            new_blob = source_bucket_obj.copy_blob(
                source_blob_obj, 
                destination_bucket_obj, 
                destination_blob
            )
            
            copy_info = {
                "source": f"gs://{source_bucket}/{source_blob}",
                "destination": f"gs://{destination_bucket}/{destination_blob}",
                "size": new_blob.size,
                "md5_hash": new_blob.md5_hash,
                "copy_time": new_blob.time_created
            }
            
            self.logger.info(f"Successfully copied blob from gs://{source_bucket}/{source_blob} to gs://{destination_bucket}/{destination_blob}")
            return copy_info
            
        except Exception as e:
            error_msg = f"Failed to copy blob: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def get_blob_metadata(self, bucket_name: str, blob_name: str) -> Dict[str, Any]:
        """
        Get detailed metadata for a specific blob.
        
        Args:
            bucket_name: Bucket name
            blob_name: Blob name
            
        Returns:
            Dictionary containing blob metadata
            
        Raises:
            RuntimeError: If operation fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            if not blob.exists():
                raise FileNotFoundError(f"Blob {blob_name} not found in bucket {bucket_name}")
            
            # Reload to get latest metadata
            blob.reload()
            
            metadata = {
                "name": blob.name,
                "bucket": blob.bucket.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "md5_hash": blob.md5_hash,
                "crc32c": blob.crc32c,
                "etag": blob.etag,
                "generation": blob.generation,
                "metageneration": blob.metageneration,
                "time_created": blob.time_created,
                "updated": blob.updated,
                "custom_metadata": blob.metadata or {},
                "public_url": f"gs://{bucket_name}/{blob_name}",
                "storage_class": blob.storage_class
            }
            
            return metadata
            
        except Exception as e:
            error_msg = f"Failed to get metadata for blob {blob_name}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def generate_signed_url(
        self, 
        bucket_name: str, 
        blob_name: str, 
        expiration_minutes: int = 60,
        method: str = "GET"
    ) -> str:
        """
        Generate a signed URL for temporary access to a blob.
        
        Args:
            bucket_name: Bucket name
            blob_name: Blob name
            expiration_minutes: URL expiration time in minutes
            method: HTTP method (GET, PUT, DELETE)
            
        Returns:
            Signed URL string
            
        Raises:
            RuntimeError: If URL generation fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            from datetime import datetime, timedelta
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            
            signed_url = blob.generate_signed_url(
                expiration=expiration,
                method=method
            )
            
            self.logger.info(f"Generated signed URL for gs://{bucket_name}/{blob_name} (expires in {expiration_minutes} minutes)")
            return signed_url
            
        except Exception as e:
            error_msg = f"Failed to generate signed URL: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def batch_upload(
        self, 
        bucket_name: str, 
        file_mappings: List[Tuple[str, str]],
        metadata: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple files in a batch operation.
        
        Args:
            bucket_name: Target bucket name
            file_mappings: List of (local_path, remote_blob_name) tuples
            metadata: Common metadata for all uploads
            
        Returns:
            List of upload result dictionaries
            
        Raises:
            RuntimeError: If batch upload fails
        """
        results = []
        errors = []
        
        for local_path, remote_blob_name in file_mappings:
            try:
                result = self.upload_file(
                    bucket_name=bucket_name,
                    file_path=local_path,
                    destination_blob_name=remote_blob_name,
                    metadata=metadata
                )
                results.append(result)
            except Exception as e:
                error_info = {
                    "local_path": local_path,
                    "remote_blob_name": remote_blob_name,
                    "error": str(e)
                }
                errors.append(error_info)
                self.logger.error(f"Failed to upload {local_path}: {e}")
        
        if errors:
            self.logger.warning(f"Batch upload completed with {len(errors)} errors out of {len(file_mappings)} files")
        else:
            self.logger.info(f"Successfully uploaded {len(results)} files")
        
        return results
    
    def get_bucket_info(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a bucket.
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            Dictionary containing bucket information
            
        Raises:
            RuntimeError: If operation fails
        """
        try:
            self._validate_bucket_name(bucket_name)
            
            bucket = self.client.bucket(bucket_name)
            bucket.reload()
            
            bucket_info = {
                "name": bucket.name,
                "location": bucket.location,
                "storage_class": bucket.storage_class,
                "time_created": bucket.time_created,
                "updated": bucket.updated,
                "metageneration": bucket.metageneration,
                "etag": bucket.etag,
                "project_number": bucket.project_number,
                "versioning_enabled": bucket.versioning_enabled,
                "labels": bucket.labels or {},
                "lifecycle_rules": [rule for rule in bucket.lifecycle_rules] if bucket.lifecycle_rules else []
            }
            
            return bucket_info
            
        except Exception as e:
            error_msg = f"Failed to get bucket info for {bucket_name}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


# Example usage and testing
if __name__ == "__main__":
    import tempfile
    
    # Example usage
    try:
        # Initialize helper
        gcs_helper = GoogleCloudStorageHelper()
        
        # Test bucket operations
        test_bucket = "my-test-bucket-12345"
        
        # Create bucket
        bucket = gcs_helper.create_bucket(test_bucket)
        print(f"Created bucket: {bucket.name}")
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("This is a test file for GCS upload")
            test_file_path = f.name
        
        try:
            # Upload file
            upload_result = gcs_helper.upload_file(
                bucket_name=test_bucket,
                file_path=test_file_path,
                destination_blob_name="test-file.txt",
                metadata={"purpose": "testing", "author": "gcs-helper"}
            )
            print(f"Upload result: {upload_result}")
            
            # List blobs
            blobs = gcs_helper.list_blobs(test_bucket, include_metadata=True)
            print(f"Blobs in bucket: {blobs}")
            
            # Get blob metadata
            metadata = gcs_helper.get_blob_metadata(test_bucket, "test-file.txt")
            print(f"Blob metadata: {metadata}")
            
        finally:
            # Cleanup
            os.unlink(test_file_path)
            gcs_helper.delete_bucket(test_bucket, force=True)
            
    except Exception as e:
        print(f"Example execution error: {e}")


class GoogleCloudStorageHelper:
    def __init__(self, credentials_path=None):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if credentials_path and os.path.isfile(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            self.client = storage.Client(project=self.project_id, credentials=credentials)
        else:
            # Use ADC if credentials file not explicitly provided
            self.client = storage.Client(project=self.project_id)

    def create_bucket(self, bucket_name):
        try:
            bucket = self.client.bucket(bucket_name)
            if not bucket.exists():
                bucket = self.client.create_bucket(bucket_name)
            return bucket
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to create bucket: {e}")

    def upload_file(self, bucket_name, file_path, destination_blob_name=None):
        if not destination_blob_name:
            destination_blob_name = os.path.basename(file_path)
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path)
            return True
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to upload file: {e}")

    def download_file(self, bucket_name, blob_name, destination_file_path):
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            Path(destination_file_path).parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(destination_file_path)
            return True
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to download file: {e}")

    def list_blobs(self, bucket_name, prefix=None):
        try:
            blobs = self.client.list_blobs(bucket_name, prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to list blobs: {e}")

    def delete_blob(self, bucket_name, blob_name):
        try:
            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to delete blob: {e}")
