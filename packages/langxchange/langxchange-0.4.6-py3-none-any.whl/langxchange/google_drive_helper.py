"""
Enhanced Google Drive Helper Class

An improved and feature-rich Google Drive API wrapper with comprehensive error handling,
logging, retry mechanisms, and additional functionality.

Author: Langxchange
Date: 2025-07-11
"""

import os
import io
import json
import logging
import mimetypes
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.credentials import Credentials


class GoogleDriveError(Exception):
    """Custom exception for Google Drive operations."""
    pass


class EnhancedGoogleDriveHelper:
    """
    Enhanced Google Drive API helper with comprehensive functionality.
    
    Features:
    - Robust error handling and retry mechanisms
    - Progress tracking for uploads/downloads
    - Batch operations
    - Advanced search functionality
    - File permissions management
    - Comprehensive logging
    - Configuration management
    - Type hints and documentation
    """
    
    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.pickle",
        scopes: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Google Drive Helper.
        
        Args:
            credentials_path: Path to Google OAuth2 credentials file
            token_path: Path to store authentication token
            scopes: List of Google Drive API scopes
            config: Configuration dictionary
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = scopes or ['https://www.googleapis.com/auth/drive']
        self.config = config or self._default_config()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize credentials and service
        self.creds: Optional[Credentials] = None
        self.service = None
        self._authenticate()
        
        self.logger.info("Google Drive Helper initialized successfully")
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration settings."""
        return {
            'max_retries': 3,
            'retry_delay': 1.0,
            'chunk_size': 1024 * 1024,  # 1MB chunks
            'timeout': 300,  # 5 minutes
            'max_workers': 4,  # For concurrent operations
            'log_level': 'INFO',
            'progress_callback': True
        }
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _authenticate(self) -> None:
        """Handle Google Drive API authentication."""
        try:
            # Load existing token
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # Refresh or create new credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.logger.info("Refreshing expired credentials")
                    self.creds.refresh(Request())
                else:
                    self.logger.info("Creating new credentials")
                    if not os.path.exists(self.credentials_path):
                        raise GoogleDriveError(f"Credentials file not found: {self.credentials_path}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.scopes
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build service
            self.service = build('drive', 'v3', credentials=self.creds)
            self.logger.info("Authentication successful")
            
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise GoogleDriveError(f"Authentication failed: {str(e)}")
    
    def _retry_operation(self, func: Callable, *args, **kwargs) -> Any:
        """
        Retry mechanism for API operations.
        
        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 1.0)
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except HttpError as e:
                if attempt == max_retries:
                    self.logger.error(f"Operation failed after {max_retries} retries: {str(e)}")
                    raise GoogleDriveError(f"API operation failed: {str(e)}")
                
                if e.resp.status in [429, 500, 502, 503, 504]:  # Retryable errors
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    time.sleep(wait_time)
                else:
                    raise GoogleDriveError(f"Non-retryable error: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                raise GoogleDriveError(f"Unexpected error: {str(e)}")
    
    def _validate_file_path(self, file_path: str) -> Path:
        """Validate and return Path object for file."""
        path = Path(file_path)
        if not path.exists():
            raise GoogleDriveError(f"File not found: {file_path}")
        if not path.is_file():
            raise GoogleDriveError(f"Path is not a file: {file_path}")
        return path
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def _progress_callback(self, current: int, total: int, operation: str = "Operation") -> None:
        """Default progress callback."""
        if self.config.get('progress_callback'):
            percentage = (current / total) * 100 if total > 0 else 0
            self.logger.info(f"{operation} progress: {percentage:.1f}% ({current}/{total} bytes)")
    
    def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """
        Create a new folder in Google Drive.
        
        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)
            description: Folder description
            
        Returns:
            Created folder ID
        """
        try:
            metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                metadata['parents'] = [parent_id]
            
            if description:
                metadata['description'] = description
            
            def create_operation():
                return self.service.files().create(body=metadata, fields='id,name').execute()
            
            folder = self._retry_operation(create_operation)
            folder_id = folder.get('id')
            
            self.logger.info(f"Created folder '{name}' with ID: {folder_id}")
            return folder_id
            
        except Exception as e:
            self.logger.error(f"Failed to create folder '{name}': {str(e)}")
            raise GoogleDriveError(f"Failed to create folder: {str(e)}")
    
    def upload_file(
        self,
        file_path: str,
        parent_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Local file path
            parent_id: Parent folder ID
            name: Custom file name (uses original if None)
            description: File description
            progress_callback: Progress callback function
            
        Returns:
            Uploaded file ID
        """
        try:
            path = self._validate_file_path(file_path)
            file_name = name or path.name
            mime_type = self._get_mime_type(str(path))
            
            file_metadata = {
                'name': file_name,
                'description': description or f"Uploaded on {datetime.now().isoformat()}"
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            media = MediaFileUpload(
                str(path),
                mimetype=mime_type,
                resumable=True,
                chunksize=self.config.get('chunk_size', 1024 * 1024)
            )
            
            def upload_operation():
                request = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,size'
                )
                
                response = None
                file_size = path.stat().st_size
                uploaded = 0
                
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        uploaded = int(status.resumable_progress)
                        if progress_callback:
                            progress_callback(uploaded, file_size)
                        else:
                            self._progress_callback(uploaded, file_size, f"Uploading {file_name}")
                
                return response
            
            result = self._retry_operation(upload_operation)
            file_id = result.get('id')
            
            self.logger.info(f"Successfully uploaded '{file_name}' with ID: {file_id}")
            return file_id
            
        except Exception as e:
            self.logger.error(f"Failed to upload file '{file_path}': {str(e)}")
            raise GoogleDriveError(f"Failed to upload file: {str(e)}")
    
    def batch_upload_files(
        self,
        file_paths: List[str],
        parent_id: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, str]]:
        """
        Upload multiple files concurrently.
        
        Args:
            file_paths: List of file paths to upload
            parent_id: Parent folder ID
            progress_callback: Progress callback function
            
        Returns:
            List of upload results with file info
        """
        results = []
        max_workers = self.config.get('max_workers', 4)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.upload_file, file_path, parent_id): file_path
                for file_path in file_paths
            }
            
            completed = 0
            total = len(file_paths)
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    file_id = future.result()
                    results.append({
                        'file_path': file_path,
                        'file_id': file_id,
                        'status': 'success'
                    })
                except Exception as e:
                    results.append({
                        'file_path': file_path,
                        'file_id': None,
                        'status': 'failed',
                        'error': str(e)
                    })
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                else:
                    self._progress_callback(completed, total, "Batch upload")
        
        self.logger.info(f"Batch upload completed: {len(results)} files processed")
        return results
    
    def download_file(
        self,
        file_id: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Google Drive file ID
            output_path: Local output path
            progress_callback: Progress callback function
        """
        try:
            def download_operation():
                # Get file metadata for size info
                metadata = self.service.files().get(fileId=file_id, fields='name,size').execute()
                file_name = metadata.get('name', 'unknown')
                file_size = int(metadata.get('size', 0))
                
                request = self.service.files().get_media(fileId=file_id)
                
                with open(output_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    downloaded = 0
                    
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            downloaded = int(status.resumable_progress)
                            if progress_callback:
                                progress_callback(downloaded, file_size)
                            else:
                                self._progress_callback(downloaded, file_size, f"Downloading {file_name}")
                
                return file_name
            
            file_name = self._retry_operation(download_operation)
            self.logger.info(f"Successfully downloaded '{file_name}' to '{output_path}'")
            
        except Exception as e:
            self.logger.error(f"Failed to download file {file_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to download file: {str(e)}")
    
    def search_files(
        self,
        query: str,
        max_results: int = 100,
        fields: str = "id,name,mimeType,size,modifiedTime,parents"
    ) -> List[Dict[str, Any]]:
        """
        Search for files in Google Drive.
        
        Args:
            query: Search query (Google Drive search syntax)
            max_results: Maximum number of results
            fields: Fields to include in results
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            def search_operation():
                results = self.service.files().list(
                    q=query,
                    pageSize=min(max_results, 1000),
                    fields=f"files({fields})"
                ).execute()
                return results.get('files', [])
            
            files = self._retry_operation(search_operation)
            self.logger.info(f"Search found {len(files)} files for query: '{query}'")
            return files
            
        except Exception as e:
            self.logger.error(f"Search failed for query '{query}': {str(e)}")
            raise GoogleDriveError(f"Search failed: {str(e)}")
    
    def list_files_in_folder(
        self,
        folder_id: str,
        include_subfolders: bool = False,
        file_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List files in a specific folder.
        
        Args:
            folder_id: Folder ID to list
            include_subfolders: Whether to include subfolders
            file_types: Filter by file types (MIME types)
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            query_parts = [f"'{folder_id}' in parents", "trashed = false"]
            
            if not include_subfolders:
                query_parts.append("mimeType != 'application/vnd.google-apps.folder'")
            
            if file_types:
                type_query = " or ".join([f"mimeType = '{t}'" for t in file_types])
                query_parts.append(f"({type_query})")
            
            query = " and ".join(query_parts)
            return self.search_files(query)
            
        except Exception as e:
            self.logger.error(f"Failed to list files in folder {folder_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to list files: {str(e)}")
    
    def get_file_metadata(
        self,
        file_id: str,
        fields: str = "id,name,mimeType,size,modifiedTime,parents,permissions"
    ) -> Dict[str, Any]:
        """
        Get detailed metadata for a file.
        
        Args:
            file_id: File ID
            fields: Fields to retrieve
            
        Returns:
            File metadata dictionary
        """
        try:
            def metadata_operation():
                return self.service.files().get(fileId=file_id, fields=fields).execute()
            
            metadata = self._retry_operation(metadata_operation)
            self.logger.info(f"Retrieved metadata for file: {metadata.get('name', file_id)}")
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to get metadata for file {file_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to get file metadata: {str(e)}")
    
    def share_file(
        self,
        file_id: str,
        email: Optional[str] = None,
        role: str = 'reader',
        type_: str = 'user'
    ) -> str:
        """
        Share a file with specific permissions.
        
        Args:
            file_id: File ID to share
            email: Email address (for user/group type)
            role: Permission role (reader, writer, commenter)
            type_: Permission type (user, group, domain, anyone)
            
        Returns:
            Permission ID
        """
        try:
            permission = {
                'role': role,
                'type': type_
            }
            
            if email and type_ in ['user', 'group']:
                permission['emailAddress'] = email
            
            def share_operation():
                return self.service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    fields='id'
                ).execute()
            
            result = self._retry_operation(share_operation)
            permission_id = result.get('id')
            
            self.logger.info(f"Shared file {file_id} with {email or type_}")
            return permission_id
            
        except Exception as e:
            self.logger.error(f"Failed to share file {file_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to share file: {str(e)}")
    
    def delete_file(self, file_id: str) -> None:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: File ID to delete
        """
        try:
            def delete_operation():
                return self.service.files().delete(fileId=file_id).execute()
            
            self._retry_operation(delete_operation)
            self.logger.info(f"Successfully deleted file: {file_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to delete file {file_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to delete file: {str(e)}")
    
    def rename_file(self, file_id: str, new_name: str) -> str:
        """
        Rename a file.
        
        Args:
            file_id: File ID to rename
            new_name: New file name
            
        Returns:
            Updated file name
        """
        try:
            file_metadata = {'name': new_name}
            
            def rename_operation():
                return self.service.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    fields='name'
                ).execute()
            
            result = self._retry_operation(rename_operation)
            updated_name = result.get('name')
            
            self.logger.info(f"Renamed file {file_id} to '{updated_name}'")
            return updated_name
            
        except Exception as e:
            self.logger.error(f"Failed to rename file {file_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to rename file: {str(e)}")
    
    def move_file(self, file_id: str, new_parent_id: str) -> None:
        """
        Move a file to a different folder.
        
        Args:
            file_id: File ID to move
            new_parent_id: New parent folder ID
        """
        try:
            # Get current parents
            file_metadata = self.get_file_metadata(file_id, fields='parents')
            previous_parents = ','.join(file_metadata.get('parents', []))
            
            def move_operation():
                return self.service.files().update(
                    fileId=file_id,
                    addParents=new_parent_id,
                    removeParents=previous_parents,
                    fields='id,parents'
                ).execute()
            
            self._retry_operation(move_operation)
            self.logger.info(f"Moved file {file_id} to folder {new_parent_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to move file {file_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to move file: {str(e)}")
    
    def copy_file(
        self,
        file_id: str,
        new_name: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Copy a file.
        
        Args:
            file_id: File ID to copy
            new_name: Name for the copy
            parent_id: Parent folder for the copy
            
        Returns:
            Copied file ID
        """
        try:
            copy_metadata = {}
            
            if new_name:
                copy_metadata['name'] = new_name
            
            if parent_id:
                copy_metadata['parents'] = [parent_id]
            
            def copy_operation():
                return self.service.files().copy(
                    fileId=file_id,
                    body=copy_metadata,
                    fields='id,name'
                ).execute()
            
            result = self._retry_operation(copy_operation)
            copy_id = result.get('id')
            copy_name = result.get('name')
            
            self.logger.info(f"Copied file {file_id} to '{copy_name}' with ID: {copy_id}")
            return copy_id
            
        except Exception as e:
            self.logger.error(f"Failed to copy file {file_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to copy file: {str(e)}")
    
    def get_storage_quota(self) -> Dict[str, Any]:
        """
        Get storage quota information.
        
        Returns:
            Storage quota information
        """
        try:
            def quota_operation():
                return self.service.about().get(fields='storageQuota').execute()
            
            result = self._retry_operation(quota_operation)
            quota = result.get('storageQuota', {})
            
            self.logger.info("Retrieved storage quota information")
            return {
                'limit': int(quota.get('limit', 0)),
                'usage': int(quota.get('usage', 0)),
                'usage_in_drive': int(quota.get('usageInDrive', 0)),
                'usage_in_drive_trash': int(quota.get('usageInDriveTrash', 0))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage quota: {str(e)}")
            raise GoogleDriveError(f"Failed to get storage quota: {str(e)}")
    
    def export_google_doc(
        self,
        file_id: str,
        export_format: str,
        output_path: str
    ) -> None:
        """
        Export Google Docs, Sheets, or Slides to various formats.
        
        Args:
            file_id: Google file ID
            export_format: Export MIME type
            output_path: Local output path
        """
        try:
            def export_operation():
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType=export_format
                )
                
                with open(output_path, 'wb') as fh:
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
            
            self._retry_operation(export_operation)
            self.logger.info(f"Exported file {file_id} to '{output_path}'")
            
        except Exception as e:
            self.logger.error(f"Failed to export file {file_id}: {str(e)}")
            raise GoogleDriveError(f"Failed to export file: {str(e)}")
    
    def close(self) -> None:
        """Clean up resources."""
        self.logger.info("Google Drive Helper session closed")


# Example usage and configuration
def create_example_config() -> Dict[str, Any]:
    """Create example configuration for Google Drive Helper."""
    return {
        'max_retries': 5,
        'retry_delay': 2.0,
        'chunk_size': 2 * 1024 * 1024,  # 2MB chunks
        'timeout': 600,  # 10 minutes
        'max_workers': 8,
        'log_level': 'DEBUG',
        'progress_callback': True
    }


# Example export formats for Google files
EXPORT_FORMATS = {
    'google_docs': {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'odt': 'application/vnd.oasis.opendocument.text',
        'txt': 'text/plain',
        'html': 'text/html'
    },
    'google_sheets': {
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ods': 'application/x-vnd.oasis.opendocument.spreadsheet',
        'pdf': 'application/pdf',
        'csv': 'text/csv',
        'tsv': 'text/tab-separated-values'
    },
    'google_slides': {
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'odp': 'application/vnd.oasis.opendocument.presentation',
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'jpeg': 'image/jpeg',
        'png': 'image/png'
    }
}


class GoogleDriveHelper:
    def __init__(self, credentials_path="credentials.json", token_path="token.pickle"):
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.creds = None
        self.token_path = token_path

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, self.scopes)
                self.creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('drive', 'v3', credentials=self.creds)

    def create_folder(self, name, parent_id=None):
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            metadata['parents'] = [parent_id]

        folder = self.service.files().create(body=metadata, fields='id').execute()
        return folder.get('id')

    def upload_file(self, file_path, parent_id=None, mime_type=None):
        file_metadata = {'name': os.path.basename(file_path)}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')

    def list_files_in_folder(self, folder_id):
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def read_file_content(self, file_id):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        return fh.read().decode()

    def download_file(self, file_id, output_path):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(output_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
        fh.close()

    def get_file_metadata(self, file_id):
        return self.service.files().get(fileId=file_id, fields='id, name, mimeType, parents').execute()

    def delete_file(self, file_id):
        self.service.files().delete(fileId=file_id).execute()

    def rename_file(self, file_id, new_name):
        file_metadata = {'name': new_name}
        updated_file = self.service.files().update(fileId=file_id, body=file_metadata).execute()
        return updated_file.get('name')
