"""
Final enhanced FAISS Helper with IVF training support and additional optimizations.
"""

import os
import uuid
import pickle
import logging
import numpy as np
import faiss
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
import warnings


class EnhancedFAISSHelper:
    """
    Production-ready FAISS-based vector store with comprehensive features.
    
    Features:
    - Multiple index types (Flat, IVF, HNSW) with auto-training
    - Robust error handling and validation
    - Persistence with metadata
    - Batch operations
    - Vector normalization support
    - Comprehensive logging
    """

    def __init__(self, dim: int = 384, index_type: str = "flat", normalize_vectors: bool = False, 
                 nlist: Optional[int] = None, auto_train: bool = True):
        """
        Initialize FAISS helper.
        
        Args:
            dim: Vector dimension
            index_type: FAISS index type ('flat', 'ivf', 'hnsw')
            normalize_vectors: Whether to normalize vectors before adding
            nlist: Number of clusters for IVF (auto-calculated if None)
            auto_train: Whether to automatically train IVF indices
        """
        if dim <= 0:
            raise ValueError(f"Dimension must be positive, got {dim}")
            
        self.dim = dim
        self.normalize_vectors = normalize_vectors
        self.index_type = index_type.lower()
        self.auto_train = auto_train
        self.nlist = nlist
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.id_list: List[str] = []
        
        # Initialize FAISS index
        self.index = self._create_index(dim, self.index_type, nlist)
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_index(self, dim: int, index_type: str, nlist: Optional[int] = None) -> faiss.Index:
        """Create FAISS index based on specified type."""
        if index_type == "flat":
            return faiss.IndexFlatL2(dim)
        elif index_type == "ivf":
            # IVF index for larger datasets
            quantizer = faiss.IndexFlatL2(dim)
            if nlist is None:
                nlist = min(4096, max(100, int(np.sqrt(10000))))  # Adaptive nlist
            return faiss.IndexIVFFlat(quantizer, dim, nlist)
        elif index_type == "hnsw":
            # HNSW index for fast approximate search
            return faiss.IndexHNSWFlat(dim, 32)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

    def _ensure_index_trained(self, vectors: np.ndarray):
        """Ensure IVF index is trained before adding vectors."""
        if (self.index_type == "ivf" and 
            hasattr(self.index, 'is_trained') and 
            not self.index.is_trained):
            
            if self.auto_train:
                # Use provided vectors for training
                train_size = min(len(vectors), max(1000, self.nlist * 39))  # FAISS recommendation
                if len(vectors) >= train_size:
                    train_vectors = vectors[:train_size]
                else:
                    # If not enough vectors, duplicate existing ones
                    multiplier = (train_size // len(vectors)) + 1
                    train_vectors = np.tile(vectors, (multiplier, 1))[:train_size]
                
                self.logger.info(f"Training IVF index with {len(train_vectors)} vectors")
                self.index.train(train_vectors)
            else:
                raise RuntimeError("IVF index requires training. Set auto_train=True or train manually.")

    def _validate_vectors(self, vectors: Union[List[List[float]], np.ndarray]) -> np.ndarray:
        """Validate and convert vectors to proper numpy array format."""
        try:
            arr = np.asarray(vectors, dtype=np.float32)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert vectors to numpy array: {e}")
        
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        elif arr.ndim != 2:
            raise ValueError(f"Vectors must be 1D or 2D array, got {arr.ndim}D")
        
        if arr.shape[1] != self.dim:
            raise ValueError(f"Vector dimension mismatch: expected {self.dim}, got {arr.shape[1]}")
        
        # Check for invalid values
        if not np.isfinite(arr).all():
            raise ValueError("Vectors contain invalid values (inf/nan)")
        
        # Normalize vectors if requested
        if self.normalize_vectors:
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            # Avoid division by zero
            norms = np.where(norms == 0, 1, norms)
            arr = arr / norms
        
        return arr

    def _validate_inputs(
        self, 
        vectors: Union[List[List[float]], np.ndarray],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[str], List[Dict[str, Any]], List[str]]:
        """Validate and prepare all inputs for insertion."""
        # Validate vectors
        arr = self._validate_vectors(vectors)
        n_vectors = arr.shape[0]
        
        # Validate documents
        if not isinstance(documents, list):
            raise TypeError("Documents must be a list")
        if len(documents) != n_vectors:
            raise ValueError(f"Number of documents ({len(documents)}) must match number of vectors ({n_vectors})")
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{} for _ in range(n_vectors)]
        elif len(metadatas) != n_vectors:
            raise ValueError(f"Number of metadatas ({len(metadatas)}) must match number of vectors ({n_vectors})")
        
        # Prepare IDs
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(n_vectors)]
        elif len(ids) != n_vectors:
            raise ValueError(f"Number of IDs ({len(ids)}) must match number of vectors ({n_vectors})")
        
        # Check for duplicate IDs
        if len(set(ids)) != len(ids):
            raise ValueError("IDs must be unique")
        
        # Check for existing IDs
        existing_ids = set(ids) & set(self.id_list)
        if existing_ids:
            raise ValueError(f"IDs already exist: {existing_ids}")
        
        return arr, documents, metadatas, ids

    def insert(
        self,
        vectors: Union[List[List[float]], np.ndarray],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Insert vectors with associated documents and metadata."""
        arr, documents, metadatas, ids = self._validate_inputs(vectors, documents, metadatas, ids)
        
        try:
            # Ensure index is trained for IVF
            self._ensure_index_trained(arr)
            
            # Add to FAISS index
            self.index.add(arr)
            
            # Store metadata
            for _id, doc, meta in zip(ids, documents, metadatas):
                self.metadata_store[_id] = {
                    "text": str(doc),
                    "metadata": dict(meta) if meta else {}
                }
                self.id_list.append(_id)
            
            self.logger.info(f"Successfully inserted {len(ids)} vectors")
            return ids
            
        except Exception as e:
            # Rollback on failure
            self.logger.error(f"Failed to insert vectors: {e}")
            rollback_start = len(self.id_list) - len(ids)
            if rollback_start >= 0:
                self.id_list = self.id_list[:rollback_start]
                for _id in ids:
                    self.metadata_store.pop(_id, None)
            raise RuntimeError(f"Failed to insert vectors: {e}")

    def insert_dataframe(self, df: pd.DataFrame, 
                        embeddings_col: str = "embeddings",
                        documents_col: str = "documents", 
                        metadata_col: str = "metadata") -> int:
        """Insert data from pandas DataFrame with improved validation."""
        if df.empty:
            self.logger.warning("Empty DataFrame provided")
            return self.count()
        
        # Validate required columns
        required_cols = [embeddings_col, documents_col, metadata_col]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        def is_valid_embedding(emb) -> bool:
            """Check if embedding is valid."""
            try:
                arr = np.asarray(emb, dtype=np.float32)
                return (arr.ndim == 1 and 
                       arr.shape[0] == self.dim and 
                       np.isfinite(arr).all())
            except (ValueError, TypeError):
                return False

        # Filter valid embeddings
        valid_mask = df[embeddings_col].apply(is_valid_embedding)
        n_invalid = (~valid_mask).sum()
        
        if n_invalid > 0:
            self.logger.warning(f"Skipping {n_invalid} rows with invalid embeddings")
            df = df[valid_mask].reset_index(drop=True)
        
        if df.empty:
            self.logger.warning("No valid embeddings found after filtering")
            return self.count()
        
        # Extract data
        embeddings = [np.asarray(emb, dtype=np.float32) for emb in df[embeddings_col]]
        documents = df[documents_col].astype(str).tolist()
        metadatas = df[metadata_col].apply(lambda x: dict(x) if isinstance(x, dict) else {}).tolist()
        
        # Insert using existing method
        self.insert(embeddings, documents, metadatas)
        
        return self.count()

    def query(self, 
             embedding_vector: Union[List[float], np.ndarray], 
             top_k: int = 5,
             include_distances: bool = False) -> List[Dict[str, Any]]:
        """Query for similar vectors."""
        if self.index.ntotal == 0:
            self.logger.warning("Index is empty")
            return []
        
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")
        
        # Validate and prepare query vector
        query_vec = self._validate_vectors([embedding_vector])
        
        try:
            # Perform search
            distances, indices = self.index.search(query_vec, min(top_k, self.count()))
            
            # Prepare results
            hits = []
            for dist, idx in zip(distances[0], indices[0]):
                if 0 <= idx < len(self.id_list):
                    _id = self.id_list[idx]
                    entry = self.metadata_store.get(_id)
                    if entry:
                        result = {
                            "id": _id,
                            "text": entry["text"],
                            "metadata": entry["metadata"]
                        }
                        if include_distances:
                            result["distance"] = float(dist)
                        hits.append(result)
            
            return hits
            
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            raise RuntimeError(f"Failed to query FAISS index: {e}")

    def query_batch(self, 
                   embedding_vectors: Union[List[List[float]], np.ndarray],
                   top_k: int = 5,
                   include_distances: bool = False) -> List[List[Dict[str, Any]]]:
        """Batch query for multiple vectors efficiently."""
        if self.index.ntotal == 0:
            return [[] for _ in range(len(embedding_vectors))]
        
        query_vecs = self._validate_vectors(embedding_vectors)
        n_queries = query_vecs.shape[0]
        
        try:
            distances, indices = self.index.search(query_vecs, min(top_k, self.count()))
            
            results = []
            for query_idx in range(n_queries):
                hits = []
                for dist, idx in zip(distances[query_idx], indices[query_idx]):
                    if 0 <= idx < len(self.id_list):
                        _id = self.id_list[idx]
                        entry = self.metadata_store.get(_id)
                        if entry:
                            result = {
                                "id": _id,
                                "text": entry["text"],
                                "metadata": entry["metadata"]
                            }
                            if include_distances:
                                result["distance"] = float(dist)
                            hits.append(result)
                results.append(hits)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch query failed: {e}")
            raise RuntimeError(f"Failed to perform batch query: {e}")

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        return self.metadata_store.get(doc_id)

    def get_by_ids(self, doc_ids: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Get multiple documents by IDs."""
        return [self.metadata_store.get(doc_id) for doc_id in doc_ids]

    def delete_by_id(self, doc_id: str) -> bool:
        """Delete document by ID (metadata only)."""
        if doc_id in self.metadata_store:
            del self.metadata_store[doc_id]
            if doc_id in self.id_list:
                self.id_list.remove(doc_id)
            return True
        return False

    def count(self) -> int:
        """Get total number of vectors in index."""
        return int(self.index.ntotal)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive index statistics."""
        stats = {
            "total_vectors": self.count(),
            "dimension": self.dim,
            "index_type": type(self.index).__name__,
            "metadata_entries": len(self.metadata_store),
            "id_list_length": len(self.id_list),
            "normalize_vectors": self.normalize_vectors,
            "auto_train": self.auto_train
        }
        
        # Add index-specific stats
        if hasattr(self.index, 'is_trained'):
            stats["is_trained"] = self.index.is_trained
        if hasattr(self.index, 'nlist'):
            stats["nlist"] = self.index.nlist
            
        return stats

    # ─── Persistence Methods ────────────────────────────────────────────────────

    def save(self, index_path: Union[str, Path], metadata_path: Optional[Union[str, Path]] = None):
        """Persist FAISS index and metadata to disk."""
        index_path = Path(index_path)
        meta_path = Path(metadata_path) if metadata_path else index_path.with_suffix(index_path.suffix + '.meta')
        
        try:
            # Create directories if they don't exist
            index_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, str(index_path))
            
            # Save metadata with comprehensive info
            metadata = {
                "id_list": self.id_list,
                "metadata_store": self.metadata_store,
                "dim": self.dim,
                "normalize_vectors": self.normalize_vectors,
                "index_type": self.index_type,
                "auto_train": self.auto_train,
                "nlist": self.nlist,
                "version": "2.1"
            }
            
            with open(meta_path, "wb") as f:
                pickle.dump(metadata, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            self.logger.info(f"Saved index to {index_path} and metadata to {meta_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save: {e}")
            raise RuntimeError(f"Failed to save FAISS index: {e}")

    def load(self, index_path: Union[str, Path], metadata_path: Optional[Union[str, Path]] = None):
        """Load FAISS index and metadata from disk."""
        index_path = Path(index_path)
        meta_path = Path(metadata_path) if metadata_path else index_path.with_suffix(index_path.suffix + '.meta')
        
        # Validate file existence
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")
        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            with open(meta_path, "rb") as f:
                data = pickle.load(f)
            
            # Validate and restore settings
            if "dim" not in data:
                raise ValueError("Invalid metadata file: missing dimension")
            
            self.dim = data["dim"]
            self.normalize_vectors = data.get("normalize_vectors", False)
            self.index_type = data.get("index_type", "flat")
            self.auto_train = data.get("auto_train", True)
            self.nlist = data.get("nlist", None)
            
            # Restore data
            self.id_list = data.get("id_list", [])
            self.metadata_store = data.get("metadata_store", {})
            
            # Validate consistency
            if len(self.id_list) != len(self.metadata_store):
                self.logger.warning("Inconsistent metadata: id_list and metadata_store sizes differ")
            
            if self.index.ntotal != len(self.id_list):
                self.logger.warning(f"Index size ({self.index.ntotal}) != metadata size ({len(self.id_list)})")
            
            self.logger.info(f"Loaded {self.count()} vectors from {index_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load: {e}")
            raise RuntimeError(f"Failed to load FAISS index: {e}")

    def clear(self):
        """Clear in-memory index and metadata."""
        try:
            self.index.reset()
            self.metadata_store.clear()
            self.id_list.clear()
            self.logger.info("Index cleared successfully")
        except Exception as e:
            self.logger.error(f"Failed to clear index: {e}")
            raise RuntimeError(f"Failed to clear index: {e}")

    def delete_persistence(self, index_path: Union[str, Path], metadata_path: Optional[Union[str, Path]] = None):
        """Delete persisted index and metadata files from disk."""
        index_path = Path(index_path)
        meta_path = Path(metadata_path) if metadata_path else index_path.with_suffix(index_path.suffix + '.meta')
        
        deleted = []
        for path in [index_path, meta_path]:
            try:
                if path.exists():
                    path.unlink()
                    deleted.append(str(path))
            except Exception as e:
                self.logger.warning(f"Failed to delete {path}: {e}")
        
        if deleted:
            self.logger.info(f"Deleted files: {deleted}")

    def rebuild_index(self, index_type: Optional[str] = None) -> int:
        """Rebuild FAISS index from scratch."""
        if not self.metadata_store:
            self.logger.warning("No data to rebuild index from")
            return 0
        
        # Use current index type if not specified
        if index_type is None:
            index_type = self.index_type
        
        # Clean up metadata
        valid_data = []
        for _id in self.id_list:
            if _id in self.metadata_store:
                valid_data.append(_id)
        
        self.id_list = valid_data
        self.metadata_store = {_id: self.metadata_store[_id] for _id in valid_data}
        
        # Create new index
        self.index_type = index_type
        self.index = self._create_index(self.dim, index_type, self.nlist)
        
        self.logger.info(f"Index rebuilt with {len(valid_data)} entries")
        return len(valid_data)


# Legacy compatibility
EnhancedFAISSHelper.insertone = EnhancedFAISSHelper.insert_dataframe





class FAISSHelper:
    """
    FAISS-based vector store with in-memory metadata and optional persistence.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.id_list: List[str] = []

    def insert(
        self,
        vectors: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        arr = np.asarray(vectors, dtype="float32")
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError(f"Invalid vectors shape {arr.shape}, expected (n, {self.dim})")
        self.index.add(arr)

        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]
        if not metadatas:
            metadatas = [{} for _ in documents]

        for _id, doc, meta in zip(ids, documents, metadatas):
            self.metadata_store[_id] = {"text": doc, "metadata": meta}
            self.id_list.append(_id)

        return ids

    def insertone(self, df: pd.DataFrame) -> int:
        def valid_emb(e):
            try:
                arr = np.asarray(e, dtype="float32")
                return arr.ndim == 1 and arr.shape[0] == self.dim
            except Exception:
                return False

        valid_mask = df["embeddings"].apply(valid_emb)
        if not valid_mask.all():
            skipped = (~valid_mask).sum()
            print(f"⚠️  Skipping {skipped} rows with invalid embeddings")
            df = df[valid_mask].reset_index(drop=True)

        documents = df["documents"].tolist()
        metadatas = df["metadata"].tolist()
        embeddings = [np.asarray(e, dtype="float32") for e in df["embeddings"].tolist()]
        arr = np.stack(embeddings, axis=0)
        self.index.add(arr)

        for _id, doc, meta in zip([str(uuid.uuid4()) for _ in documents], documents, metadatas):
            self.metadata_store[_id] = {"text": doc, "metadata": meta}
            self.id_list.append(_id)

        return int(self.index.ntotal)

    def query(self, embedding_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        arr = np.asarray(embedding_vector, dtype="float32")
        if arr.ndim == 1:
            vec = arr.reshape(1, -1)
        elif arr.ndim == 2 and arr.shape == (1, self.dim):
            vec = arr
        else:
            raise ValueError(f"Invalid embedding_vector shape {arr.shape}, expected 1D of length {self.dim} or shape (1, {self.dim})")

        try:
            result = self.index.search(vec, top_k)
            if isinstance(result, tuple) and len(result) == 2:
                _, I = result
            else:
                raise RuntimeError(f"Unexpected return from faiss.Index.search: {result!r}")
        except Exception as e:
            raise RuntimeError(f"[❌ ERROR] Failed to query FAISS: {e}")

        hits = []
        for idx in I[0]:
            if 0 <= idx < len(self.id_list):
                _id = self.id_list[idx]
                entry = self.metadata_store[_id]
                hits.append({
                    "id": _id,
                    "text": entry["text"],
                    "metadata": entry["metadata"]
                })
        return hits

    def count(self) -> int:
        return int(self.index.ntotal)

    # ─── Persistence Methods ────────────────────────────────────────────────────

    def save(self, index_path: str, metadata_path: Optional[str] = None):
        faiss.write_index(self.index, index_path)
        meta_file = metadata_path or index_path + ".meta"
        with open(meta_file, "wb") as f:
            pickle.dump({
                "id_list": self.id_list,
                "metadata_store": self.metadata_store,
                "dim": self.dim
            }, f)

    def load(self, index_path: str, metadata_path: Optional[str] = None):
        # 1) Load FAISS index
        if not os.path.isfile(index_path):
            raise FileNotFoundError(f"Index file not found: {index_path}")
        self.index = faiss.read_index(index_path)

        # 2) Load metadata
        meta_file = metadata_path or f"{index_path}.meta"
        if not os.path.isfile(meta_file):
            raise FileNotFoundError(f"Metadata file not found: {meta_file}")
        with open(meta_file, "rb") as f:
            data = pickle.load(f)

        # 3) Override helper.dim to match persisted index
        stored_dim = data.get("dim")
        if stored_dim is None:
            raise RuntimeError(f"'dim' not found in metadata file: {meta_file}")
        self.dim = stored_dim

        # 4) Restore IDs & metadata
        self.id_list = data.get("id_list", [])
        self.metadata_store = data.get("metadata_store", {})

    def clear(self):
        self.index.reset()
        self.metadata_store.clear()
        self.id_list.clear()

    def delete_persistence(self, index_path: str, metadata_path: Optional[str] = None):
        for path in [index_path, metadata_path or f"{index_path}.meta"]:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass


# # langxchange/faiss_helper.py

# import os
# import uuid
# import pickle
# import numpy as np
# import faiss
# import pandas as pd
# from typing import List, Dict, Any, Optional


# class FAISSHelper:
#     """
#     FAISS-based vector store with in-memory metadata and optional persistence.
#     """

#     def __init__(self, dim: int = 384):
#         self.dim = dim
#         self.index = faiss.IndexFlatL2(dim)
#         self.metadata_store: Dict[str, Dict[str, Any]] = {}
#         self.id_list: List[str] = []

#     def insert(
#         self,
#         vectors: List[List[float]],
#         documents: List[str],
#         metadatas: Optional[List[Dict[str, Any]]] = None,
#         ids: Optional[List[str]] = None
#     ) -> List[str]:
#         # ... existing insert implementation ...
#         arr = np.asarray(vectors, dtype="float32")
#         if arr.ndim != 2 or arr.shape[1] != self.dim:
#             raise ValueError(f"Invalid vectors shape {arr.shape}, expected (n, {self.dim})")
#         self.index.add(arr)
#         if not ids:
#             ids = [str(uuid.uuid4()) for _ in documents]
#         if not metadatas:
#             metadatas = [{} for _ in documents]
#         for _id, doc, meta in zip(ids, documents, metadatas):
#             self.metadata_store[_id] = {"text": doc, "metadata": meta}
#             self.id_list.append(_id)
#         return ids

#     def insertone(self, df: pd.DataFrame) -> int:
#         # ... existing insertone implementation ...
#         def valid_emb(e):
#             try:
#                 arr = np.asarray(e, dtype="float32")
#                 return arr.ndim == 1 and arr.shape[0] == self.dim
#             except Exception:
#                 return False

#         valid_mask = df["embeddings"].apply(valid_emb)
#         if not valid_mask.all():
#             skipped = (~valid_mask).sum()
#             print(f"⚠️  Skipping {skipped} rows with invalid embeddings")
#             df = df[valid_mask].reset_index(drop=True)

#         documents = df["documents"].tolist()
#         metadatas = df["metadata"].tolist()
#         embeddings = [np.asarray(e, dtype="float32") for e in df["embeddings"].tolist()]
#         arr = np.stack(embeddings, axis=0)
#         self.index.add(arr)
#         for _id, doc, meta in zip([str(uuid.uuid4()) for _ in documents], documents, metadatas):
#             self.metadata_store[_id] = {"text": doc, "metadata": meta}
#             self.id_list.append(_id)
#         return int(self.index.ntotal)

#     def query(self, embedding_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
#         # ... existing query implementation ...
#         if self.index.ntotal == 0:
#             return []
#         arr = np.asarray(embedding_vector, dtype="float32")
#         if arr.ndim == 1:
#             vec = arr.reshape(1, -1)
#         elif arr.ndim == 2 and arr.shape == (1, self.dim):
#             vec = arr
#         else:
#             raise ValueError(f"Invalid embedding_vector shape {arr.shape}, expected (dim,) or (1, dim)")
#         result = self.index.search(vec, top_k)
#         if not (isinstance(result, tuple) and len(result) == 2):
#             raise RuntimeError(f"Unexpected FAISS return: {result!r}")
#         D, I = result
#         hits = []
#         for idx in I[0]:
#             if 0 <= idx < len(self.id_list):
#                 _id = self.id_list[idx]
#                 entry = self.metadata_store[_id]
#                 hits.append({
#                     "id": _id,
#                     "text": entry["text"],
#                     "metadata": entry["metadata"]
#                 })
#         return hits

#     def count(self) -> int:
#         return int(self.index.ntotal)

#     # ─── Persistence Methods ────────────────────────────────────────────────────

#     def save(self, index_path: str, metadata_path: Optional[str] = None):
#         """
#         Persist FAISS index and metadata to disk.
#         """
#         faiss.write_index(self.index, index_path)
#         meta_file = metadata_path or index_path + ".meta"
#         with open(meta_file, "wb") as f:
#             pickle.dump({
#                 "id_list": self.id_list,
#                 "metadata_store": self.metadata_store,
#                 "dim": self.dim
#             }, f)

#     def load(self, index_path: str, metadata_path: Optional[str] = None):
#         """
#         Load FAISS index and metadata from disk.
#         """
#         if not os.path.isfile(index_path):
#             raise FileNotFoundError(f"Index file not found: {index_path}")
#         self.index = faiss.read_index(index_path)
#         meta_file = metadata_path or index_path + ".meta"
#         if not os.path.isfile(meta_file):
#             raise FileNotFoundError(f"Metadata file not found: {meta_file}")
#         with open(meta_file, "rb") as f:
#             data = pickle.load(f)
#         if data.get("dim") != self.dim:
#             raise RuntimeError(f"Dimension mismatch: index dim={data.get('dim')} vs helper dim={self.dim}")
#         self.id_list = data["id_list"]
#         self.metadata_store = data["metadata_store"]

#     def clear(self):
#         """
#         Clear in-memory index and metadata (does not delete disk files).
#         """
#         self.index.reset()
#         self.metadata_store.clear()
#         self.id_list.clear()

#     def delete_persistence(self, index_path: str, metadata_path: Optional[str] = None):
#         """
#         Delete persisted index and metadata files from disk.
#         """
#         for path in [index_path, metadata_path or index_path + ".meta"]:
#             try:
#                 os.remove(path)
#             except FileNotFoundError:
#                 pass
