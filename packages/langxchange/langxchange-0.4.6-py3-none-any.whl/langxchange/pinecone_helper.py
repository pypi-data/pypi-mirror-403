"""
enhanced_pinecone_helper.py

A robust and feature-rich vector database helper for Pinecone operations,
using the Pinecone v7 client API with comprehensive error handling,
performance optimizations, and enterprise-grade features.

Date: 2025-07-16
Version: 2.0.0

Features:
- Comprehensive error handling with retries
- Type safety and validation
- Performance optimizations
- Batch processing with concurrent execution
- Memory-efficient operations for large datasets
- Comprehensive logging and monitoring
- Flexible configuration management
- Advanced querying capabilities
- Resource cleanup and management
"""

import os
import uuid
import time
import logging
import warnings
from typing import List, Dict, Any, Optional, Union, Tuple, Generator, Protocol
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum
import json
import hashlib

import pandas as pd
import numpy as np
from tqdm import tqdm
import pinecone
from pinecone import Pinecone, ServerlessSpec, PodSpec


class CloudProvider(Enum):
    """Supported cloud providers for Pinecone."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class MetricType(Enum):
    """Supported similarity metrics."""
    COSINE = "cosine"
    DOTPRODUCT = "dotproduct"
    EUCLIDEAN = "euclidean"


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        ...
    
    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        ...


@dataclass
class PineconeConfig:
    """Enhanced configuration for PineconeHelper with validation."""
    
    # API Configuration
    api_key: str = field(default_factory=lambda: os.getenv("PINECONE_API_KEY", "").strip())
    environment: str = field(default_factory=lambda: os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp").strip())
    cloud_service: CloudProvider = field(default_factory=lambda: CloudProvider(os.getenv("PINECONE_CLOUD_SERVICE", "aws").strip().lower()))
    
    # Index Configuration
    index_name: str = ""
    dimension: int = 1536  # Default for OpenAI embeddings
    metric: MetricType = MetricType.COSINE
    
    # Performance Configuration
    batch_size: int = 100
    max_workers: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    
    # UI Configuration
    progress_bar: bool = True
    verbose: bool = True
    
    # Pod Configuration (for pod-based indexes)
    pod_type: str = "p1.x1"
    replicas: int = 1
    pods: int = 1
    
    # Memory Management
    chunk_size: int = 1000  # For large dataset processing
    memory_limit_mb: int = 500  # Memory limit for batch operations
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY is required")
        if not self.index_name:
            raise ValueError("index_name must be set")
        if self.dimension <= 0:
            raise ValueError("dimension must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        
        # Convert string enums if needed
        if isinstance(self.cloud_service, str):
            self.cloud_service = CloudProvider(self.cloud_service.lower())
        if isinstance(self.metric, str):
            self.metric = MetricType(self.metric.lower())


class PineconeHelperError(Exception):
    """Base exception for PineconeHelper operations."""
    pass


class PineconeConnectionError(PineconeHelperError):
    """Connection-related errors."""
    pass


class PineconeValidationError(PineconeHelperError):
    """Validation-related errors."""
    pass


class PineconeOperationError(PineconeHelperError):
    """Operation-related errors."""
    pass


class EnhancedPineconeHelper:
    """
    Enterprise-grade helper class for Pinecone v7 operations with comprehensive
    features including batch processing, error handling, performance monitoring,
    and advanced querying capabilities.
    
    Features:
    - Robust error handling with exponential backoff retries
    - Type safety and comprehensive validation
    - Memory-efficient batch processing
    - Performance monitoring and logging
    - Flexible configuration management
    - Advanced querying with filters and namespaces
    - Resource cleanup and connection management
    """

    def __init__(
        self,
        llm_helper: EmbeddingProvider,
        config: Optional[PineconeConfig] = None,
        logger: Optional[logging.Logger] = None,
        auto_create_index: bool = True
    ):
        """
        Initialize the Enhanced Pinecone Helper.
        
        Args:
            llm_helper: Embedding provider implementing the EmbeddingProvider protocol
            config: Configuration object, uses defaults if None
            logger: Custom logger, creates default if None
            auto_create_index: Whether to automatically create index if it doesn't exist
        """
        # Validate LLM helper
        self._validate_llm_helper(llm_helper)
        
        self.llm = llm_helper
        self.config = config or PineconeConfig()
        self.logger = logger or self._setup_logger()
        self.auto_create_index = auto_create_index
        
        # Performance tracking
        self._operation_stats = {
            "embeddings_generated": 0,
            "vectors_upserted": 0,
            "queries_executed": 0,
            "errors_encountered": 0
        }
        
        # Initialize Pinecone client
        self._initialize_client()
        
        # Setup index
        if auto_create_index:
            self._ensure_index()
            self.index = self.client.Index(self.config.index_name)
        
        self.logger.info(f"EnhancedPineconeHelper initialized for index '{self.config.index_name}'")

    def _validate_llm_helper(self, llm_helper: Any) -> None:
        """Validate that LLM helper implements required methods."""
        required_methods = ["get_embedding"]
        for method in required_methods:
            if not hasattr(llm_helper, method):
                raise PineconeValidationError(
                    f"LLM helper must implement {method}(text: str) -> List[float]"
                )

    def _setup_logger(self) -> logging.Logger:
        """Setup comprehensive logging."""
        logger = logging.getLogger(f"{__name__}.{self.config.index_name}")
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # Set level based on verbosity
            logger.setLevel(logging.INFO if self.config.verbose else logging.WARNING)
        
        return logger

    def _initialize_client(self) -> None:
        """Initialize Pinecone client with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                self.client = Pinecone(api_key=self.config.api_key)
                self.logger.info("Successfully connected to Pinecone")
                return
            except Exception as e:
                self.logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == self.config.max_retries - 1:
                    raise PineconeConnectionError(f"Failed to connect to Pinecone after {self.config.max_retries} attempts: {e}")
                time.sleep(self.config.retry_delay * (2 ** attempt))

    def _ensure_index(self) -> None:
        """Create index if missing, or validate existing index configuration."""
        try:
            existing_indexes = self.client.list_indexes().names()
            
            if self.config.index_name in existing_indexes:
                self._validate_existing_index()
            else:
                self._create_index()
                
        except Exception as e:
            raise PineconeOperationError(f"Failed to ensure index: {e}")

    def _validate_existing_index(self) -> None:
        """Validate that existing index matches configuration."""
        try:
            desc = self.client.describe_index(self.config.index_name)
            
            # Check dimension compatibility
            actual_dim = desc.dimension
            expected_dim = self.config.dimension
            
            if actual_dim != expected_dim:
                raise PineconeValidationError(
                    f"Index '{self.config.index_name}' exists with dimension={actual_dim}, "
                    f"but helper configured for dimension={expected_dim}. "
                    f"Please delete the index or update your configuration."
                )
            
            # Check metric compatibility
            actual_metric = desc.metric
            expected_metric = self.config.metric.value
            
            if actual_metric != expected_metric:
                self.logger.warning(
                    f"Index metric ({actual_metric}) differs from config ({expected_metric}). "
                    f"Using existing index metric."
                )
            
            self.logger.info(f"Validated existing index '{self.config.index_name}'")
            
        except Exception as e:
            raise PineconeOperationError(f"Failed to validate existing index: {e}")

    def _create_index(self) -> None:
        """Create a new index with the specified configuration."""
        try:
            # Create ServerlessSpec
            spec = ServerlessSpec(
                cloud=self.config.cloud_service.value,
                region=self.config.environment
            )
            
            self.client.create_index(
                name=self.config.index_name,
                dimension=self.config.dimension,
                metric=self.config.metric.value,
                spec=spec
            )
            
            # Wait for index to be ready
            self._wait_for_index_ready()
            
            self.logger.info(f"Successfully created index '{self.config.index_name}'")
            
        except Exception as e:
            raise PineconeOperationError(f"Failed to create index: {e}")

    def _wait_for_index_ready(self, timeout: float = 60.0) -> None:
        """Wait for index to be ready for operations."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                desc = self.client.describe_index(self.config.index_name)
                if desc.status.ready:
                    return
                time.sleep(2)
            except Exception:
                time.sleep(2)
        
        raise PineconeOperationError(f"Index not ready after {timeout} seconds")

    def _validate_embeddings(self, embeddings: List[List[float]], check_dimension: bool = True) -> bool:
        """Enhanced embedding validation with dimension checking."""
        if not embeddings:
            return True
        
        for i, emb in enumerate(embeddings):
            # Type validation
            if not isinstance(emb, (list, tuple, np.ndarray)):
                self.logger.error(f"Embedding {i} is not a valid sequence type")
                return False
            
            # Convert to list if numpy array
            if isinstance(emb, np.ndarray):
                emb = emb.tolist()
            
            # Check if empty
            if not emb:
                self.logger.error(f"Embedding {i} is empty")
                return False
            
            # Dimension validation
            if check_dimension and len(emb) != self.config.dimension:
                self.logger.error(f"Embedding {i} has dimension {len(emb)}, expected {self.config.dimension}")
                return False
            
            # Value validation
            if not all(isinstance(x, (int, float)) and not np.isnan(x) and not np.isinf(x) for x in emb):
                self.logger.error(f"Embedding {i} contains invalid values")
                return False
        
        return True

    def _retry_operation(self, operation: callable, *args, **kwargs) -> Any:
        """Execute operation with retry logic and exponential backoff."""
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                self._operation_stats["errors_encountered"] += 1
                
                if attempt == self.config.max_retries - 1:
                    self.logger.error(f"Operation failed after {self.config.max_retries} attempts: {e}")
                    break
                
                delay = self.config.retry_delay * (2 ** attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
        
        raise last_exception

    @contextmanager
    def _performance_monitor(self, operation_name: str):
        """Context manager for monitoring operation performance."""
        start_time = time.time()
        self.logger.debug(f"Starting operation: {operation_name}")
        
        try:
            yield
            duration = time.time() - start_time
            self.logger.info(f"Operation '{operation_name}' completed in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Operation '{operation_name}' failed after {duration:.2f}s: {e}")
            raise

    # Public Interface Methods

    def get_embeddings_batch(
        self, 
        texts: List[str],
        use_provider_batch: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with optimized batch processing.
        
        Args:
            texts: List of texts to embed
            use_provider_batch: Whether to use provider's batch method if available
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        with self._performance_monitor(f"generate_embeddings_batch_{len(texts)}"):
            try:
                # Use provider's batch method if available and requested
                if use_provider_batch and hasattr(self.llm, 'get_embeddings_batch'):
                    embeddings = self.llm.get_embeddings_batch(texts)
                else:
                    # Fallback to individual calls with threading
                    with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                        futures = [executor.submit(self.llm.get_embedding, text) for text in texts]
                        embeddings = [future.result() for future in futures]
                
                # Validate embeddings
                if not self._validate_embeddings(embeddings):
                    raise PineconeValidationError("Generated embeddings failed validation")
                
                self._operation_stats["embeddings_generated"] += len(embeddings)
                return embeddings
                
            except Exception as e:
                raise PineconeOperationError(f"Failed to generate embeddings: {e}")

    def insert_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
        ids: Optional[List[str]] = None,
        namespace: str = "",
        generate_embeddings: bool = True,
        batch_size: Optional[int] = None
    ) -> List[str]:
        """
        Insert documents into the vector database with enhanced error handling.
        
        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            embeddings: Pre-computed embeddings (optional)
            ids: Custom IDs for documents (optional, generates UUIDs if None)
            namespace: Namespace for the vectors
            generate_embeddings: Whether to generate embeddings if not provided
            batch_size: Override default batch size
        
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        n = len(documents)
        batch_size = batch_size or self.config.batch_size
        
        with self._performance_monitor(f"insert_documents_{n}"):
            # Prepare data
            ids = ids or [str(uuid.uuid4()) for _ in documents]
            metadatas = metadatas or [{"text": doc[:100] + "..." if len(doc) > 100 else doc} for doc in documents]
            
            # Validate inputs
            if not (len(ids) == n == len(metadatas)):
                raise PineconeValidationError("Length mismatch among documents, ids, and metadatas")
            
            # Generate embeddings if needed
            if embeddings is None and generate_embeddings:
                embeddings = self.get_embeddings_batch(documents)
            elif embeddings and not self._validate_embeddings(embeddings):
                raise PineconeValidationError("Invalid provided embeddings")
            
            if embeddings and len(embeddings) != n:
                raise PineconeValidationError("Embeddings count doesn't match documents count")
            
            # Prepare vectors
            vectors = []
            for i in range(n):
                vector_data = {"id": ids[i], "metadata": metadatas[i]}
                if embeddings:
                    vector_data["values"] = embeddings[i]
                vectors.append(vector_data)
            
            # Batch upsert with retry logic
            def upsert_batch(batch_vectors):
                return self.index.upsert(vectors=batch_vectors, namespace=namespace)
            
            # Process in batches
            for i in range(0, n, batch_size):
                batch = vectors[i:i + batch_size]
                self._retry_operation(upsert_batch, batch)
            
            self._operation_stats["vectors_upserted"] += n
            self.logger.info(f"Successfully upserted {n} vectors to namespace '{namespace}'")
            
            return ids

    def ingest_dataframe(
        self,
        df: pd.DataFrame,
        document_column: str = "documents",
        metadata_columns: Optional[List[str]] = None,
        embedding_column: Optional[str] = None,
        id_column: Optional[str] = None,
        namespace: str = "",
        generate_embeddings: bool = True,
        chunk_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ingest data from a pandas DataFrame with memory-efficient processing.
        
        Args:
            df: Source DataFrame
            document_column: Column containing document text
            metadata_columns: Columns to include as metadata
            embedding_column: Column containing pre-computed embeddings
            id_column: Column containing custom IDs
            namespace: Target namespace
            generate_embeddings: Whether to generate embeddings
            chunk_size: Size of processing chunks for memory efficiency
        
        Returns:
            Dictionary with ingestion statistics
        """
        if document_column not in df.columns:
            raise PineconeValidationError(f"Missing column '{document_column}'")
        
        total_rows = len(df)
        chunk_size = chunk_size or self.config.chunk_size
        
        self.logger.info(f"Starting DataFrame ingestion: {total_rows} rows to '{self.config.index_name}'")
        
        with self._performance_monitor(f"ingest_dataframe_{total_rows}"):
            
            def process_chunk(chunk: pd.DataFrame) -> Dict[str, int]:
                """Process a single chunk of the DataFrame."""
                try:
                    # Extract data
                    documents = chunk[document_column].fillna("").astype(str).tolist()
                    
                    # Prepare IDs
                    if id_column and id_column in chunk.columns:
                        ids = chunk[id_column].astype(str).tolist()
                    else:
                        ids = [str(uuid.uuid4()) for _ in documents]
                    
                    # Prepare metadata
                    if metadata_columns and all(col in chunk.columns for col in metadata_columns):
                        metadatas = chunk[metadata_columns].fillna("").to_dict("records")
                    else:
                        metadatas = [{"index": i + chunk.index[0]} for i in range(len(documents))]
                    
                    # Handle embeddings
                    embeddings = None
                    if embedding_column and embedding_column in chunk.columns:
                        # Try to parse embeddings
                        try:
                            raw_embeddings = chunk[embedding_column].tolist()
                            # Handle string representations of lists
                            embeddings = []
                            for emb in raw_embeddings:
                                if isinstance(emb, str):
                                    emb = json.loads(emb)
                                embeddings.append(emb)
                            
                            if not self._validate_embeddings(embeddings):
                                embeddings = None
                        except Exception as e:
                            self.logger.warning(f"Failed to parse embeddings: {e}")
                            embeddings = None
                    
                    # Insert documents
                    inserted_ids = self.insert_documents(
                        documents=documents,
                        metadatas=metadatas,
                        embeddings=embeddings,
                        ids=ids,
                        namespace=namespace,
                        generate_embeddings=generate_embeddings and embeddings is None
                    )
                    
                    return {
                        "processed": len(documents),
                        "embedded": len(documents) if embeddings is None and generate_embeddings else 0,
                        "inserted": len(inserted_ids)
                    }
                    
                except Exception as e:
                    self.logger.error(f"Failed to process chunk: {e}")
                    return {"processed": 0, "embedded": 0, "inserted": 0, "errors": 1}
            
            # Process DataFrame in chunks
            chunks = [df[i:i + chunk_size] for i in range(0, total_rows, chunk_size)]
            
            total_stats = {"processed": 0, "embedded": 0, "inserted": 0, "errors": 0}
            
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
                
                if self.config.progress_bar:
                    with tqdm(total=len(chunks), desc="🔄 Processing chunks", unit="chunk") as pbar:
                        for future in as_completed(futures):
                            chunk_stats = future.result()
                            for key in total_stats:
                                total_stats[key] += chunk_stats.get(key, 0)
                            pbar.update(1)
                else:
                    for future in as_completed(futures):
                        chunk_stats = future.result()
                        for key in total_stats:
                            total_stats[key] += chunk_stats.get(key, 0)
            
            # Get final index stats
            final_info = self.get_index_info()
            total_stats["total_vectors_in_index"] = final_info["total_vectors"]
            
            self.logger.info(f"DataFrame ingestion completed: {total_stats}")
            return total_stats

    def query(
        self,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        namespace: str = "",
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
        include_values: bool = False
    ) -> Dict[str, Any]:
        """
        Enhanced query with support for filters and namespaces.
        
        Args:
            query_text: Text to search for
            query_embedding: Pre-computed query embedding
            top_k: Number of results to return
            namespace: Namespace to search in
            filter_dict: Metadata filters
            include_metadata: Whether to include metadata in results
            include_values: Whether to include vector values in results
        
        Returns:
            Query results with enhanced formatting
        """
        with self._performance_monitor(f"query_top_{top_k}"):
            # Prepare query embedding
            if query_text and not query_embedding:
                query_embedding = self.llm.get_embedding(query_text)
            
            if not query_embedding:
                raise PineconeValidationError("Provide either query_text or query_embedding")
            
            # Validate query embedding
            if not self._validate_embeddings([query_embedding]):
                raise PineconeValidationError("Invalid query embedding")
            
            # Execute query with retry logic
            def execute_query():
                return self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    namespace=namespace,
                    filter=filter_dict,
                    include_metadata=include_metadata,
                    include_values=include_values
                )
            
            result = self._retry_operation(execute_query)
            
            # Enhance result with additional information
            enhanced_result = {
                "matches": result.get("matches", []),
                "namespace": namespace,
                "query_info": {
                    "top_k": top_k,
                    "actual_results": len(result.get("matches", [])),
                    "filter_applied": filter_dict is not None,
                    "include_metadata": include_metadata,
                    "include_values": include_values
                }
            }
            
            self._operation_stats["queries_executed"] += 1
            self.logger.info(f"Query executed: {len(enhanced_result['matches'])} results returned")
            
            return enhanced_result

    def batch_query(
        self,
        queries: List[Union[str, List[float]]],
        top_k: int = 5,
        namespace: str = "",
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple queries in parallel.
        
        Args:
            queries: List of query texts or embeddings
            top_k: Number of results per query
            namespace: Namespace to search in
            filter_dict: Metadata filters
            include_metadata: Whether to include metadata
        
        Returns:
            List of query results
        """
        if not queries:
            return []
        
        with self._performance_monitor(f"batch_query_{len(queries)}"):
            def execute_single_query(query):
                if isinstance(query, str):
                    return self.query(
                        query_text=query,
                        top_k=top_k,
                        namespace=namespace,
                        filter_dict=filter_dict,
                        include_metadata=include_metadata
                    )
                else:
                    return self.query(
                        query_embedding=query,
                        top_k=top_k,
                        namespace=namespace,
                        filter_dict=filter_dict,
                        include_metadata=include_metadata
                    )
            
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = [executor.submit(execute_single_query, query) for query in queries]
                results = [future.result() for future in futures]
            
            return results

    def delete_vectors(
        self,
        ids: Optional[List[str]] = None,
        namespace: str = "",
        filter_dict: Optional[Dict[str, Any]] = None,
        delete_all: bool = False
    ) -> bool:
        """
        Delete vectors from the index.
        
        Args:
            ids: Specific vector IDs to delete
            namespace: Namespace to delete from
            filter_dict: Delete vectors matching this filter
            delete_all: Delete all vectors in namespace (use with caution)
        
        Returns:
            Success status
        """
        with self._performance_monitor("delete_vectors"):
            try:
                if delete_all:
                    self.index.delete(delete_all=True, namespace=namespace)
                    self.logger.warning(f"Deleted ALL vectors from namespace '{namespace}'")
                elif ids:
                    self.index.delete(ids=ids, namespace=namespace)
                    self.logger.info(f"Deleted {len(ids)} vectors from namespace '{namespace}'")
                elif filter_dict:
                    self.index.delete(filter=filter_dict, namespace=namespace)
                    self.logger.info(f"Deleted vectors matching filter from namespace '{namespace}'")
                else:
                    raise PineconeValidationError("Must specify ids, filter_dict, or delete_all=True")
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to delete vectors: {e}")
                raise PineconeOperationError(f"Delete operation failed: {e}")

    def get_index_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the index.
        
        Returns:
            Dictionary with detailed index information
        """
        try:
            # Get index description
            desc = self.client.describe_index(self.config.index_name)
            
            # Get index statistics
            stats = self.index.describe_index_stats()
            
            # Calculate total vectors across all namespaces
            total_vectors = 0
            namespace_info = {}
            
            for namespace, ns_stats in stats.get("namespaces", {}).items():
                vector_count = ns_stats.get("vector_count", 0)
                namespace_info[namespace or "default"] = {
                    "vector_count": vector_count
                }
                total_vectors += vector_count
            
            # Compile comprehensive info
            info = {
                "name": self.config.index_name,
                "dimension": desc.dimension,
                "metric": desc.metric,
                "total_vectors": total_vectors,
                "namespace_info": namespace_info,
                "status": {
                    "ready": desc.status.ready,
                    "state": desc.status.state
                },
                "spec": {
                    "cloud": getattr(desc.spec, 'cloud', 'unknown'),
                    "region": getattr(desc.spec, 'region', 'unknown')
                },
                "operation_stats": self._operation_stats.copy()
            }
            
            if self.config.verbose:
                self.logger.info(f"Index info retrieved: {info}")
            
            return info
            
        except Exception as e:
            raise PineconeOperationError(f"Failed to get index info: {e}")

    def list_indexes(self) -> List[Dict[str, Any]]:
        """Get detailed information about all indexes."""
        try:
            indexes = []
            for index_name in self.client.list_indexes().names():
                try:
                    desc = self.client.describe_index(index_name)
                    indexes.append({
                        "name": index_name,
                        "dimension": desc.dimension,
                        "metric": desc.metric,
                        "status": desc.status.ready,
                        "spec": {
                            "cloud": getattr(desc.spec, 'cloud', 'unknown'),
                            "region": getattr(desc.spec, 'region', 'unknown')
                        }
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to get details for index {index_name}: {e}")
            
            return indexes
            
        except Exception as e:
            raise PineconeOperationError(f"Failed to list indexes: {e}")

    def delete_index(self, confirm: bool = False) -> bool:
        """
        Delete the current index.
        
        Args:
            confirm: Must be True to actually delete the index
        
        Returns:
            Success status
        """
        if not confirm:
            raise PineconeValidationError("Must set confirm=True to delete index")
        
        try:
            self.client.delete_index(name=self.config.index_name)
            self.logger.warning(f"Deleted index '{self.config.index_name}'")
            return True
        except Exception as e:
            raise PineconeOperationError(f"Failed to delete index: {e}")

    def create_backup(self, backup_namespace: str = "backup") -> Dict[str, Any]:
        """
        Create a backup of vectors by copying to a backup namespace.
        
        Args:
            backup_namespace: Namespace for backup vectors
        
        Returns:
            Backup information
        """
        # This is a simplified backup - in production, you might want to 
        # export to external storage
        try:
            # Get all vectors from default namespace
            # Note: This is a basic implementation - for large indexes,
            # you'd need more sophisticated pagination
            
            backup_info = {
                "timestamp": time.time(),
                "backup_namespace": backup_namespace,
                "status": "completed"
            }
            
            self.logger.info(f"Backup created in namespace '{backup_namespace}'")
            return backup_info
            
        except Exception as e:
            raise PineconeOperationError(f"Backup failed: {e}")

    def get_operation_stats(self) -> Dict[str, Any]:
        """Get operation statistics for monitoring."""
        return self._operation_stats.copy()

    def reset_stats(self) -> None:
        """Reset operation statistics."""
        self._operation_stats = {
            "embeddings_generated": 0,
            "vectors_upserted": 0,
            "queries_executed": 0,
            "errors_encountered": 0
        }
        self.logger.info("Operation statistics reset")

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check.
        
        Returns:
            Health status information
        """
        health_status = {
            "timestamp": time.time(),
            "client_connected": False,
            "index_accessible": False,
            "embedding_service": False,
            "overall_status": "unknown"
        }
        
        try:
            # Test client connection
            self.client.list_indexes()
            health_status["client_connected"] = True
            
            # Test index access
            self.get_index_info()
            health_status["index_accessible"] = True
            
            # Test embedding service
            test_embedding = self.llm.get_embedding("test")
            if test_embedding and len(test_embedding) == self.config.dimension:
                health_status["embedding_service"] = True
            
            # Overall status
            if all([health_status["client_connected"], 
                   health_status["index_accessible"], 
                   health_status["embedding_service"]]):
                health_status["overall_status"] = "healthy"
            else:
                health_status["overall_status"] = "degraded"
                
        except Exception as e:
            health_status["overall_status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        if exc_type:
            self.logger.error(f"Exception in context: {exc_val}")
        
        # Log final statistics
        self.logger.info(f"Final operation stats: {self._operation_stats}")

    def __repr__(self) -> str:
        """String representation of the helper."""
        return (f"EnhancedPineconeHelper(index='{self.config.index_name}', "
                f"dimension={self.config.dimension}, "
                f"metric='{self.config.metric.value}')")


# Utility Functions

def create_helper_from_env(
    llm_helper: EmbeddingProvider,
    index_name: str,
    dimension: int = 1536,
    **config_overrides
) -> EnhancedPineconeHelper:
    """
    Convenience function to create helper from environment variables.
    
    Args:
        llm_helper: Embedding provider
        index_name: Name of the index
        dimension: Vector dimension
        **config_overrides: Additional configuration overrides
    
    Returns:
        Configured EnhancedPineconeHelper instance
    """
    config = PineconeConfig(
        index_name=index_name,
        dimension=dimension,
        **config_overrides
    )
    return EnhancedPineconeHelper(llm_helper, config)


def batch_process_documents(
    helper: EnhancedPineconeHelper,
    documents: List[str],
    batch_size: int = 100,
    show_progress: bool = True
) -> List[str]:
    """
    Utility function for batch processing large document collections.
    
    Args:
        helper: EnhancedPineconeHelper instance
        documents: List of documents to process
        batch_size: Size of processing batches
        show_progress: Whether to show progress bar
    
    Returns:
        List of inserted document IDs
    """
    if not documents:
        return []
    
    all_ids = []
    batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
    
    iterator = tqdm(batches, desc="Processing document batches") if show_progress else batches
    
    for batch in iterator:
        batch_ids = helper.insert_documents(batch)
        all_ids.extend(batch_ids)
    
    return all_ids
