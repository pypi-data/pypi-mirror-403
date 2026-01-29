import os
import logging
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
import pandas as pd
from pymongo import MongoClient, errors
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import InsertManyResult, InsertOneResult, UpdateResult, DeleteResult


class EnhancedMongoHelper:
    """
    Enhanced MongoDB helper class with improved error handling, type hints, 
    and additional functionality for database operations.
    """
    
    def __init__(
        self, 
        db_name: Optional[str] = None, 
        collection_name: Optional[str] = None,
        uri: Optional[str] = None,
        connect_timeout: int = 5000,
        server_selection_timeout: int = 5000
    ):
        """
        Initialize MongoDB helper with connection parameters.
        
        Args:
            db_name: Database name (falls back to env MONGO_DB or 'langxchange')
            collection_name: Collection name (falls back to env MONGO_COLLECTION or 'documents')
            uri: MongoDB URI (falls back to env MONGO_URI or localhost)
            connect_timeout: Connection timeout in milliseconds
            server_selection_timeout: Server selection timeout in milliseconds
        """
        self.uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = db_name or os.getenv("MONGO_DB", "langxchange")
        self.collection_name = collection_name or os.getenv("MONGO_COLLECTION", "documents")
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Connection configuration
        self.client_config = {
            'connectTimeoutMS': connect_timeout,
            'serverSelectionTimeoutMS': server_selection_timeout,
            'retryWrites': True
        }
        
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._collection: Optional[Collection] = None
        
        # Initialize connection
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            self._client = MongoClient(self.uri, **self.client_config)
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[self.db_name]
            self._collection = self._db[self.collection_name]
            self.logger.info(f"Successfully connected to MongoDB: {self.db_name}.{self.collection_name}")
        except errors.ServerSelectionTimeoutError as e:
            raise ConnectionError(f"Failed to connect to MongoDB server: {e}")
        except errors.ConfigurationError as e:
            raise ConnectionError(f"MongoDB configuration error: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error connecting to MongoDB: {e}")
    
    @property
    def client(self) -> MongoClient:
        """Get MongoDB client, reconnect if necessary."""
        if self._client is None:
            self._connect()
        return self._client
    
    @property
    def db(self) -> Database:
        """Get database object."""
        if self._db is None:
            self._connect()
        return self._db
    
    @property
    def collection(self) -> Collection:
        """Get collection object."""
        if self._collection is None:
            self._connect()
        return self._collection
    
    def ping(self) -> bool:
        """Test database connection."""
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            self.logger.error(f"Ping failed: {e}")
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._collection = None
            self.logger.info("MongoDB connection closed")
    
    @contextmanager
    def get_collection(self, collection_name: str):
        """Context manager for working with different collections."""
        original_collection = self._collection
        original_name = self.collection_name
        try:
            self.collection_name = collection_name
            self._collection = self._db[collection_name]
            yield self._collection
        finally:
            self._collection = original_collection
            self.collection_name = original_name
    
    def insert_one(self, document: Dict[str, Any]) -> InsertOneResult:
        """
        Insert a single document.
        
        Args:
            document: Document to insert
            
        Returns:
            InsertOneResult object
        """
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary")
        
        try:
            result = self.collection.insert_one(document)
            self.logger.info(f"Inserted document with ID: {result.inserted_id}")
            return result
        except errors.DuplicateKeyError as e:
            raise ValueError(f"Duplicate key error: {e}")
        except errors.WriteError as e:
            raise RuntimeError(f"Write error during insert: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to insert document: {e}")
    
    def insert_many(
        self, 
        documents: Union[List[Dict[str, Any]], pd.DataFrame],
        ordered: bool = True
    ) -> InsertManyResult:
        """
        Insert multiple documents.
        
        Args:
            documents: List of documents or DataFrame to insert
            ordered: If True, stop on first error; if False, continue on errors
            
        Returns:
            InsertManyResult object
        """
        if not documents:
            raise ValueError("Documents list cannot be empty")
        
        # Convert DataFrame to list of dictionaries
        if isinstance(documents, pd.DataFrame):
            documents = documents.to_dict(orient="records")
        
        if not isinstance(documents, list):
            raise ValueError("Documents must be a list or DataFrame")
        
        # Validate all documents are dictionaries
        if not all(isinstance(doc, dict) for doc in documents):
            raise ValueError("All documents must be dictionaries")
        
        try:
            result = self.collection.insert_many(documents, ordered=ordered)
            self.logger.info(f"Inserted {len(result.inserted_ids)} documents")
            return result
        except errors.BulkWriteError as e:
            raise RuntimeError(f"Bulk write error: {e.details}")
        except Exception as e:
            raise RuntimeError(f"Failed to insert documents: {e}")
    
    # Legacy method for backward compatibility
    def insert(self, documents: Union[List[Dict[str, Any]], pd.DataFrame]) -> List[Any]:
        """Legacy insert method for backward compatibility."""
        result = self.insert_many(documents)
        return result.inserted_ids
    
    def find_one(
        self, 
        filter_query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document.
        
        Args:
            filter_query: Query filter
            projection: Fields to include/exclude
            
        Returns:
            Document or None
        """
        try:
            return self.collection.find_one(filter_query or {}, projection)
        except Exception as e:
            raise RuntimeError(f"Failed to find document: {e}")
    
    def query(
        self, 
        filter_query: Optional[Dict[str, Any]] = None,
        projection: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        sort: Optional[List[tuple]] = None,
        as_dataframe: bool = True
    ) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Query documents with enhanced options.
        
        Args:
            filter_query: Query filter
            projection: Fields to include/exclude
            limit: Maximum number of documents to return
            sort: Sort specification [(field, direction), ...]
            as_dataframe: Return as DataFrame if True, else as list
            
        Returns:
            DataFrame or list of documents
        """
        try:
            cursor = self.collection.find(filter_query or {}, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            if limit:
                cursor = cursor.limit(limit)
            
            documents = list(cursor)
            
            if as_dataframe:
                return pd.DataFrame(documents)
            return documents
            
        except Exception as e:
            raise RuntimeError(f"Failed to query documents: {e}")
    
    def update_one(
        self,
        filter_query: Dict[str, Any],
        update_doc: Dict[str, Any],
        upsert: bool = False
    ) -> UpdateResult:
        """
        Update a single document.
        
        Args:
            filter_query: Query to match document
            update_doc: Update operations
            upsert: Create document if not found
            
        Returns:
            UpdateResult object
        """
        try:
            result = self.collection.update_one(filter_query, update_doc, upsert=upsert)
            self.logger.info(f"Updated {result.modified_count} document(s)")
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to update document: {e}")
    
    def update_many(
        self,
        filter_query: Dict[str, Any],
        update_doc: Dict[str, Any]
    ) -> UpdateResult:
        """
        Update multiple documents.
        
        Args:
            filter_query: Query to match documents
            update_doc: Update operations
            
        Returns:
            UpdateResult object
        """
        try:
            result = self.collection.update_many(filter_query, update_doc)
            self.logger.info(f"Updated {result.modified_count} document(s)")
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to update documents: {e}")
    
    def delete_one(self, filter_query: Dict[str, Any]) -> DeleteResult:
        """
        Delete a single document.
        
        Args:
            filter_query: Query to match document
            
        Returns:
            DeleteResult object
        """
        try:
            result = self.collection.delete_one(filter_query)
            self.logger.info(f"Deleted {result.deleted_count} document(s)")
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to delete document: {e}")
    
    def delete_many(self, filter_query: Dict[str, Any]) -> DeleteResult:
        """
        Delete multiple documents.
        
        Args:
            filter_query: Query to match documents
            
        Returns:
            DeleteResult object
        """
        try:
            result = self.collection.delete_many(filter_query)
            self.logger.info(f"Deleted {result.deleted_count} document(s)")
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to delete documents: {e}")
    
    def count_documents(self, filter_query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching query.
        
        Args:
            filter_query: Query filter
            
        Returns:
            Number of matching documents
        """
        try:
            return self.collection.count_documents(filter_query or {})
        except Exception as e:
            raise RuntimeError(f"Failed to count documents: {e}")
    
    # Legacy method for backward compatibility
    def count(self) -> int:
        """Legacy count method for backward compatibility."""
        return self.count_documents()
    
    def create_index(
        self,
        keys: Union[str, List[tuple]],
        unique: bool = False,
        sparse: bool = False,
        background: bool = True
    ) -> str:
        """
        Create an index on the collection.
        
        Args:
            keys: Index specification
            unique: Create unique index
            sparse: Create sparse index
            background: Create index in background
            
        Returns:
            Index name
        """
        try:
            result = self.collection.create_index(
                keys,
                unique=unique,
                sparse=sparse,
                background=background
            )
            self.logger.info(f"Created index: {result}")
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to create index: {e}")
    
    def list_indexes(self) -> List[Dict[str, Any]]:
        """List all indexes on the collection."""
        try:
            return list(self.collection.list_indexes())
        except Exception as e:
            raise RuntimeError(f"Failed to list indexes: {e}")
    
    def drop_collection(self) -> None:
        """Drop the current collection."""
        try:
            self.collection.drop()
            self.logger.info(f"Dropped collection: {self.collection_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to drop collection: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            return self.db.command("collStats", self.collection_name)
        except Exception as e:
            raise RuntimeError(f"Failed to get collection stats: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        try:
            self.close()
        except:
            pass  # Ignore errors during cleanup




class MongoHelper:
    def __init__(self, db_name=None, collection_name=None):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = db_name or os.getenv("MONGO_DB", "langxchange")
        self.collection_name = collection_name or os.getenv("MONGO_COLLECTION", "documents")

        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
        except Exception as e:
            raise ConnectionError(f"[❌ ERROR] Failed to connect to MongoDB: {e}")

    def insert(self, documents: list):
        try:
            if isinstance(documents, pd.DataFrame):
                documents = documents.to_dict(orient="records")
            result = self.collection.insert_many(documents)
            return result.inserted_ids
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to insert documents into MongoDB: {e}")

    def query(self, filter_query: dict = {}, projection: dict = None):
        try:
            cursor = self.collection.find(filter_query, projection)
            return pd.DataFrame(list(cursor))
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to query MongoDB: {e}")

    def count(self):
        try:
            return self.collection.count_documents({})
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to count documents: {e}")
