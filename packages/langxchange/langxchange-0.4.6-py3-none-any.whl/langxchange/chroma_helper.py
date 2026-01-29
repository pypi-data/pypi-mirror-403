"""
ChromaHelper - An improved vector database helper for ChromaDB operations.

This module provides a robust interface for managing ChromaDB collections
with features including batch processing, error handling, and type safety.

Author: Langxchange
Date: 2025-07-02
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import pandas as pd
from tqdm import tqdm
import chromadb
from chromadb.config import Settings


@dataclass
class ChromaConfig:
    """Configuration class for ChromaHelper."""
    persist_directory: str = "./chroma_store"
    batch_size: int = 100
    max_workers: int = 10
    progress_bar: bool = True


class ChromaHelperError(Exception):
    """Custom exception for ChromaHelper operations."""
    pass


class EnhancedChromaHelper:
    """
    A comprehensive helper class for ChromaDB operations with improved error handling,
    type safety, and performance optimizations.
    """
    
    def __init__(
        self, 
        llm_helper: Any, 
        config: Optional[ChromaConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize ChromaHelper with LLM helper and configuration.
        
        Args:
            llm_helper: An object with 'get_embedding' method for text embeddings
            config: Configuration object for ChromaHelper settings
            logger: Optional logger instance for debugging
            
        Raises:
            ChromaHelperError: If llm_helper doesn't have required methods
        """
        if not llm_helper or not hasattr(llm_helper, "get_embedding"):
            raise ChromaHelperError(
                "A valid LLM helper instance with a 'get_embedding' method is required."
            )

        self.llm_helper = llm_helper
        self.config = config or self._load_config_from_env()
        self.logger = logger or self._setup_logger()
        
        try:
            self.client = chromadb.PersistentClient(path=self.config.persist_directory)
            self.logger.info(f"ChromaDB client initialized with path: {self.config.persist_directory}")
        except Exception as e:
            raise ChromaHelperError(f"Failed to initialize ChromaDB client: {e}")

    def _load_config_from_env(self) -> ChromaConfig:
        """Load configuration from environment variables."""
        return ChromaConfig(
            persist_directory=os.getenv("CHROMA_PERSIST_PATH", "./chroma_store"),
            batch_size=int(os.getenv("CHROMA_BATCH_SIZE", "100")),
            max_workers=int(os.getenv("CHROMA_THREADS", "10")),
            progress_bar=os.getenv("CHROMA_PROGRESS", "true").lower() == "true"
        )

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger for ChromaHelper."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _validate_embeddings(self, embeddings: List[List[float]]) -> bool:
        """
        Validate that embeddings are properly formatted.
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            bool: True if all embeddings are valid
        """
        return all(
            isinstance(emb, (list, tuple)) and len(emb) > 0 
            and all(isinstance(x, (int, float)) for x in emb)
            for emb in embeddings
        )

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a batch of texts with error handling.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            ChromaHelperError: If embedding generation fails
        """
        if not texts:
            return []
            
        try:
            embeddings = [self.llm_helper.get_embedding(text) for text in texts]
            if not self._validate_embeddings(embeddings):
                raise ChromaHelperError("Generated embeddings are invalid")
            return embeddings
        except Exception as e:
            raise ChromaHelperError(f"Failed to generate embeddings: {e}")

    def embed_texts_batched(self, texts: list) -> list:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
            
        Note:
            This method provides the exact signature from the original ChromaHelper
            while leveraging the improved error handling internally.
        """
        return self.get_embeddings_batch(texts)

    def create_collection(self, collection_name: str) -> Any:
        """
        Create or get a ChromaDB collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            ChromaDB collection object
            
        Raises:
            ChromaHelperError: If collection creation fails
        """
        try:
            collection = self.client.get_or_create_collection(name=collection_name)
            self.logger.info(f"Collection '{collection_name}' ready")
            return collection
        except Exception as e:
            raise ChromaHelperError(f"Failed to create collection '{collection_name}': {e}")

    def insert_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
        ids: Optional[List[str]] = None,
        generate_embeddings: bool = True
    ) -> List[str]:
        """
        Insert documents into a ChromaDB collection with flexible options.
        
        Args:
            collection_name: Name of the target collection
            documents: List of document texts
            metadatas: Optional metadata for each document
            embeddings: Optional pre-computed embeddings
            ids: Optional custom IDs for documents
            generate_embeddings: Whether to generate embeddings if not provided
            
        Returns:
            List of document IDs that were inserted
            
        Raises:
            ChromaHelperError: If insertion fails
        """
        if not documents:
            self.logger.warning("No documents provided for insertion")
            return []

        collection = self.create_collection(collection_name)
        
        # Generate IDs if not provided
        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Generate default metadata if not provided
        if not metadatas:
            metadatas = [{"index": i} for i in range(len(documents))]
        
        # Generate embeddings if not provided and requested
        if not embeddings and generate_embeddings:
            embeddings = self.get_embeddings_batch(documents)
        elif embeddings and not self._validate_embeddings(embeddings):
            raise ChromaHelperError("Provided embeddings are invalid")

        # Validate input lengths
        if metadatas and len(metadatas) != len(documents):
            raise ChromaHelperError("Metadata count must match document count")
        if embeddings and len(embeddings) != len(documents):
            raise ChromaHelperError("Embeddings count must match document count")
        if len(ids) != len(documents):
            raise ChromaHelperError("IDs count must match document count")

        try:
            insert_params = {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas
            }
            
            if embeddings:
                insert_params["embeddings"] = embeddings
                
            collection.add(**insert_params)
            self.logger.info(f"Successfully inserted {len(documents)} documents into '{collection_name}'")
            return ids
            
        except Exception as e:
            raise ChromaHelperError(f"Failed to insert documents: {e}")

    def ingest_dataframe(
        self,
        df: pd.DataFrame,
        collection_name: str,
        document_column: str = "documents",
        metadata_columns: Optional[List[str]] = None,
        embedding_column: Optional[str] = None,
        generate_embeddings: bool = True
    ) -> int:
        """
        Ingest a DataFrame into ChromaDB with batch processing and progress tracking.
        
        Args:
            df: DataFrame containing documents and metadata
            collection_name: Name of the target collection
            document_column: Column name containing document texts
            metadata_columns: List of columns to use as metadata
            embedding_column: Column name containing pre-computed embeddings
            generate_embeddings: Whether to generate embeddings if not provided
            
        Returns:
            Total number of documents in the collection after ingestion
            
        Raises:
            ChromaHelperError: If ingestion fails
        """
        if df.empty:
            self.logger.warning("Empty DataFrame provided for ingestion")
            return 0

        if document_column not in df.columns:
            raise ChromaHelperError(f"Document column '{document_column}' not found in DataFrame")

        # Prepare metadata
        if metadata_columns:
            missing_cols = [col for col in metadata_columns if col not in df.columns]
            if missing_cols:
                raise ChromaHelperError(f"Metadata columns not found: {missing_cols}")
        
        total_records = len(df)
        self.logger.info(
            f"Starting ingestion of {total_records} records into collection '{collection_name}'"
        )

        def process_batch(batch_df: pd.DataFrame) -> int:
            """Process a single batch of documents."""
            try:
                documents = batch_df[document_column].tolist()
                
                # Prepare metadata
                if metadata_columns:
                    metadatas = batch_df[metadata_columns].to_dict(orient="records")
                else:
                    metadatas = [{"batch_index": i} for i in range(len(batch_df))]
                
                # Handle embeddings
                embeddings = None
                if embedding_column and embedding_column in batch_df.columns:
                    embeddings = batch_df[embedding_column].tolist()
                    if not self._validate_embeddings(embeddings):
                        self.logger.warning("Some embeddings in batch are invalid, will regenerate")
                        embeddings = None

                self.insert_documents(
                    collection_name=collection_name,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                    generate_embeddings=generate_embeddings
                )
                return len(batch_df)
                
            except Exception as e:
                self.logger.error(f"Failed to process batch: {e}")
                return 0

        # Split into batches
        batches = [
            df[i:i + self.config.batch_size] 
            for i in range(0, total_records, self.config.batch_size)
        ]

        # Process batches with threading
        processed_count = 0
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [executor.submit(process_batch, batch) for batch in batches]
            
            if self.config.progress_bar:
                with tqdm(total=len(batches), desc="🔄 Ingesting batches", unit="batch") as pbar:
                    for future in as_completed(futures):
                        result = future.result()
                        processed_count += result
                        pbar.update(1)
            else:
                for future in as_completed(futures):
                    processed_count += future.result()

        self.logger.info(f"Ingestion completed. Processed {processed_count} documents")
        return self.get_collection_count(collection_name)

    def ingest_to_chroma(self, df: pd.DataFrame, collection_name: str, engine: str = "llm") -> int:
        """
        Ingest a DataFrame into ChromaDB using the original method signature.
        
        Args:
            df: DataFrame containing documents and metadata (expects "documents" column)
            collection_name: Name of the target collection
            engine: Processing engine (maintained for compatibility, not used)
            
        Returns:
            Total number of documents in the collection after ingestion
            
        Note:
            This method provides the exact signature from the original ChromaHelper
            while leveraging the improved batch processing and error handling internally.
        """
        if df.empty:
            self.logger.warning("Empty DataFrame provided for ingestion")
            return 0

        if "documents" not in df.columns:
            raise ChromaHelperError("DataFrame must contain a 'documents' column")

        collection = self.create_collection(collection_name)
        total_records = len(df)
        
        print(f"🚀 Ingesting {total_records} records into collection '{collection_name}' using engine '{engine}'")

        def process_batch(batch_df: pd.DataFrame) -> int:
            """Process a single batch of documents."""
            try:
                texts = batch_df["documents"].tolist()
                ids = [str(uuid.uuid4()) for _ in texts]
                metadatas = batch_df.to_dict(orient="records")

                try:
                    embeddings = self.embed_texts_batched(texts)
                    collection.add(
                        ids=ids,
                        documents=texts,
                        embeddings=embeddings,
                        metadatas=metadatas
                    )
                    return len(batch_df)
                except Exception as e:
                    print(f"❌ Failed to add batch: {e}")
                    return 0
                    
            except Exception as e:
                self.logger.error(f"Failed to process batch: {e}")
                print(f"❌ Failed to add batch: {e}")
                return 0

        # Use configuration for batch processing
        batch_size = self.config.batch_size
        max_workers = self.config.max_workers
        
        batches = [df[i:i + batch_size] for i in range(0, total_records, batch_size)]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_batch, batch) for batch in batches]
            with tqdm(total=len(batches), desc="🔄 Ingesting", unit="batch") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)

        return len(collection.get()["ids"])

    def query(
        self,
        collection_name: str,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        include_metadata: bool = True,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        return self.query_collection(
            collection_name = collection_name,
            query_text=query_text,
            query_embedding = query_embedding,
            top_k = top_k,
            include_metadata = include_metadata,
            where_filter = where_filter)


    def query_collection(
        self,
        collection_name: str,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        include_metadata: bool = True,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query a ChromaDB collection with flexible input options.
        
        Args:
            collection_name: Name of the collection to query
            query_text: Text to search for (will generate embedding)
            query_embedding: Pre-computed query embedding
            top_k: Number of results to return
            include_metadata: Whether to include metadata in results
            where_filter: Optional metadata filter for results
            
        Returns:
            Query results from ChromaDB
            
        Raises:
            ChromaHelperError: If query fails
        """
        if not query_text and not query_embedding:
            raise ChromaHelperError("Either query_text or query_embedding must be provided")

        collection = self.create_collection(collection_name)
        
        # Generate embedding if only text provided
        if query_text and not query_embedding:
            query_embedding = self.llm_helper.get_embedding(query_text)

        if not query_embedding:
            raise ChromaHelperError("Failed to obtain query embedding")

        try:
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas"] if include_metadata else ["documents"]
            }
            
            if where_filter:
                query_params["where"] = where_filter

            results = collection.query(**query_params)
            self.logger.info(f"Query returned {len(results.get('documents', []))} results")
            return results
            
        except Exception as e:
            raise ChromaHelperError(f"Failed to query collection '{collection_name}': {e}")

    def get_collection_count(self, collection_name: str) -> int:
        """
        Get the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of documents in the collection
            
        Raises:
            ChromaHelperError: If operation fails
        """
        try:
            collection = self.create_collection(collection_name)
            count = len(collection.get()["ids"])
            self.logger.info(f"Collection '{collection_name}' contains {count} documents")
            return count
        except Exception as e:
            raise ChromaHelperError(f"Failed to get collection count: {e}")

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from ChromaDB.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            ChromaHelperError: If deletion fails
        """
        try:
            self.client.delete_collection(name=collection_name)
            self.logger.info(f"Collection '{collection_name}' deleted successfully")
            return True
        except Exception as e:
            raise ChromaHelperError(f"Failed to delete collection '{collection_name}': {e}")

    def list_collections(self) -> List[str]:
        """
        List all collections in the ChromaDB instance.
        
        Returns:
            List of collection names
            
        Raises:
            ChromaHelperError: If operation fails
        """
        try:
            collections = self.client.list_collections()
            collection_names = [col.name for col in collections]
            self.logger.info(f"Found {len(collection_names)} collections")
            return collection_names
        except Exception as e:
            raise ChromaHelperError(f"Failed to list collections: {e}")

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary containing collection information
            
        Raises:
            ChromaHelperError: If operation fails
        """
        try:
            collection = self.create_collection(collection_name)
            
            # Get basic info
            all_data = collection.get(include=["documents", "metadatas", "embeddings"])
            count = len(all_data["ids"])
            
            info = {
                "name": collection_name,
                "count": count,
                "has_documents": bool(all_data.get("documents")),
                "has_metadata": bool(all_data.get("metadatas")),
                "has_embeddings": bool(all_data.get("embeddings"))
            }
            
            # Add embedding dimension if available
            if all_data.get("embeddings") and len(all_data["embeddings"]) > 0:
                info["embedding_dimension"] = len(all_data["embeddings"][0])
            
            self.logger.info(f"Retrieved info for collection '{collection_name}'")
            return info
            
        except Exception as e:
            raise ChromaHelperError(f"Failed to get collection info: {e}")




#langxchange.chroma_helper
# import os
# import uuid
# import pandas as pd
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from tqdm import tqdm
# import chromadb
# from chromadb.config import Settings


class ChromaHelper:
    
    def __init__(self, llm_helper, persist_directory=None):
        if not llm_helper or not hasattr(llm_helper, "get_embedding"):
            raise ValueError("❌ A valid LLM helper instance with a 'get_embedding' method is required.")

        self.llm_helper = llm_helper
        persist_directory = persist_directory or os.getenv("CHROMA_PERSIST_PATH", "./chroma_store")
        self.client = chromadb.PersistentClient(path = persist_directory)

    def embed_texts_batched(self, texts: list) -> list:
        return [self.llm_helper.get_embedding(text) for text in texts]

    def ingest_to_chroma(self, df: pd.DataFrame, collection_name: str, engine: str = "llm"):
        batch_size = int(os.getenv("CHROMA_BATCH_SIZE", 100))
        max_workers = int(os.getenv("CHROMA_THREADS", 10))

        collection = self.client.get_or_create_collection(name=collection_name)
        total_records = len(df)
        print(f"🚀 Ingesting {total_records} records into collection '{collection_name}' using engine '{engine}'")

        def process_batch(batch_df):
            texts = batch_df["documents"].tolist()
            ids = [str(uuid.uuid4()) for _ in texts]
            metadatas = batch_df.to_dict(orient="records")

            try:
                embeddings = self.embed_texts_batched(texts)
                collection.add(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                return len(batch_df)
            except Exception as e:
                print(f"❌ Failed to add batch: {e}")
                return 0

        batches = [df[i:i + batch_size] for i in range(0, total_records, batch_size)]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_batch, batch) for batch in batches]
            with tqdm(total=len(batches), desc="🔄 Ingesting", unit="batch") as pbar:
                for future in as_completed(futures):
                    future.result()
                    pbar.update(1)

        return len(collection.get()["ids"])
    
    

    #     return len(collection.get()["ids"])
    def insertone(
        self,
        df: pd.DataFrame,
        collection_name: str
    ) -> int:
        """
        Inserts rows of a DataFrame into a Chroma collection.
        Expects df columns:
          - "documents": List[str]
          - "metadata":  List[dict]
          - "embeddings": List[List[float]]
        Drops any row whose embeddings are not a non-empty list.
        Returns the total count in the collection afterwards.
        """
        collection = self.client.get_or_create_collection(name=collection_name)

        # Validate and filter embeddings
        valid_mask = df["embeddings"].apply(
            lambda emb: isinstance(emb, (list, tuple)) and len(emb) > 0
        )
        if not valid_mask.all():
            skipped = (~valid_mask).sum()
            print(f"⚠️  Skipping {skipped} rows with invalid embeddings")
            df = df[valid_mask].reset_index(drop=True)

        texts     = df["documents"].tolist()
        metadatas = df["metadata"].tolist()
        embeddings= df["embeddings"].tolist()
        ids       = [str(uuid.uuid4()) for _ in texts]

        try:
            collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to insert into Chroma: {e}")

        return len(collection.get()["ids"])
    

    def insert(self, collection_name: str, documents: list, embeddings: list, metadatas: list = None, ids: list = None):
        collection = self.client.get_or_create_collection(name=collection_name)
        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]
        if not metadatas:
            metadatas = [{"default": "value"} for _ in documents]
        else:
            metadatas = [{"default": "value", **md} if not md else md for md in metadatas]

        try:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to insert into Chroma: {e}")
        return ids

    def query(self, collection_name: str, embedding_vector: list, top_k: int = 5, include_metadata: bool = True):
        collection = self.client.get_or_create_collection(name=collection_name)
        try:
            return collection.query(
                query_embeddings=[embedding_vector],
                n_results=top_k,
                include=["documents", "metadatas"] if include_metadata else ["documents"]
            )
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to query Chroma: {e}")

    def get_collection_count(self, collection_name: str):
        collection = self.client.get_or_create_collection(name=collection_name)
        try:
            return len(collection.get()["ids"])
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Could not get Chroma collection count: {e}")
