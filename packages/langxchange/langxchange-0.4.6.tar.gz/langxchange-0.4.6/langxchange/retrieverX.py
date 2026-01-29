# langxchange/EnhancedRetrieverX.py

# from typing import List, Dict, Any, Optional, Tuple
# from sentence_transformers import CrossEncoder
"""
Improved EnhancedRetrieverX: Two-stage retrieval with vector search and cross-encoder re-ranking.

This module provides a flexible and robust retrieval system that combines:
1. Vector similarity search (first stage)
2. Optional cross-encoder re-ranking (second stage)

Key improvements:
- Protocol-based vector database abstraction
- Enhanced error handling and validation
- Better type safety with specific type hints
- Improved documentation and code organization
- More consistent scoring system
- Configurable retrieval parameters
"""

from typing import List, Dict, Any, Optional, Protocol, Union,Tuple
from dataclasses import dataclass
import logging
from sentence_transformers import CrossEncoder
import numpy as np



# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Represents a single retrieval result."""
    document: str
    metadata: Dict[str, Any]
    score: float
    rank: Optional[int] = None


class VectorDatabaseProtocol(Protocol):
    """Protocol defining the interface for vector databases."""
    
    def query(self, *args, **kwargs) -> Dict[str, Any]:
        """Query the vector database and return results."""
        ...


# class EmbedderProtocol(Protocol):
#     """Protocol defining the interface for text embedders."""
    
#     def embed(self, **kwargs) -> Union[List[List[float]], np.ndarray, Dict[str, Any]]:
#         """Embed a list of texts and return their vector representations."""
#         ...

#     # def get_embedding(self, **kwargs) -> Union[List[List[float]], np.ndarray, Dict[str, Any]]:
#     #     """Embed a list of texts and return their vector representations."""
#         ...
    
#     # def get_embedding(self, **kwargs) -> List[float]:
#     #     """Embed a list of texts and return their vector representations."""
#     #     ...


class VectorDatabaseAdapter:
    """Adapter to standardize different vector database interfaces."""
    
    def __init__(self, vector_db: Any, db_type: str = "auto"):
        """
        Initialize the adapter.
        
        Args:
            vector_db: The vector database instance
            db_type: Type of database ("chroma", "faiss", or "auto" for auto-detection)
        """
        self.vector_db = vector_db
        self.db_type = db_type
        # self,
        # collection_name: str,
        # query_text: Optional[str] = None,
        # query_embedding: Optional[List[float]] = None,
        # top_k: int = 5,
        # include_metadata: bool = True,
        # where_filter: Optional[Dict[str, Any]] = None
    def query(
        self, 
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None, 
        top_k: int=5, 
        collection_name: Optional[str] = None,
        include_metadata: bool = True,
    ) -> Dict[str, List[Any]]:
        """
        Standardized query interface for different vector databases.
        
        Args:
            embedding_vector: Query embedding vector
            top_k: Number of results to retrieve
            collection_name: Collection name (for Chroma-like databases)
            
        Returns:
            Standardized result dictionary with 'documents', 'metadatas', and 'scores'
        """
        try:
            # Try Chroma-like interface first
            if collection_name is not None:
                result = self.vector_db.query(
                    collection_name=collection_name,
                    query_embedding=query_embedding,
                    top_k=top_k,
                    include_metadata=True
                )
                return self._normalize_chroma_result(result)
            else:
                # Try FAISS-like interface
                result = self.vector_db.query(query_embedding, top_k)
                return self._normalize_faiss_result(result)
                
        except TypeError as e:
            logger.error(f"Vector database query failed: {e}")
            raise RuntimeError(f"Incompatible vector database interface: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during vector database query: {e}")
            raise RuntimeError(f"Vector database query error: {e}")
    
    def _normalize_chroma_result(self, result: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Normalize Chroma-style results."""
        if not isinstance(result, dict):
            raise ValueError(f"Expected dict result from Chroma, got {type(result)}")
            
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        # Chroma typically returns distances, convert to similarity scores
        distances = result.get("distances", [])
        scores = [1.0 / (1.0 + dist) if dist >= 0 else 0.0 for dist in distances] if distances else []
        
        return {
            "documents": documents,
            "metadatas": metadatas or [{}] * len(documents),
            "scores": scores or [0.0] * len(documents)
        }
    
    def _normalize_faiss_result(self, result: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
        """Normalize FAISS-style results."""
        if not isinstance(result, list):
            raise ValueError(f"Expected list result from FAISS, got {type(result)}")
            
        documents = [item.get("text", "") for item in result]
        metadatas = [item.get("metadata", {}) for item in result]
        scores = [item.get("score", 0.0) for item in result]
        
        return {
            "documents": documents,
            "metadatas": metadatas,
            "scores": scores
        }


class EnhancedRetrieverX:
    """
    Enhanced two-stage retrieval system with vector search and cross-encoder re-ranking.
    
    This class provides a flexible and robust retrieval pipeline that:
    1. Converts queries to embeddings
    2. Performs vector similarity search
    3. Optionally re-ranks results using cross-encoder models
    
    Features:
    - Support for multiple vector database backends
    - Configurable re-ranking with cross-encoders
    - Robust error handling and validation
    - Detailed logging and metrics
    - Type-safe interfaces with protocols
    """

    def __init__(
        self,
        vector_db: VectorDatabaseProtocol,
        embedder: None, #query_embedding: Optional[List[float]] = None,
        reranker_model: Optional[str] = None,
        use_rerank: bool = True,
        rerank_multiplier: float = 2.0,
        min_score_threshold: float = 0.0,
        db_type: str = "auto"
    ):
        """
        Initialize the EnhancedRetrieverX system.

        Args:
            vector_db: Vector database instance (must implement query method)
            embedder: Text embedder instance (must implement embed method)
            reranker_model: Name/path of cross-encoder model for re-ranking
            use_rerank: Whether to enable cross-encoder re-ranking
            rerank_multiplier: Multiplier for initial retrieval when re-ranking
            min_score_threshold: Minimum score threshold for results
            db_type: Type of vector database ("chroma", "faiss", "auto")
        """
        # Validate inputs
        if not hasattr(vector_db, 'query'):
            raise ValueError("vector_db must have a 'query' method")
        if not hasattr(embedder, 'get_embedding'):
            raise ValueError("embedder must have an 'get_embedding' method")
        if rerank_multiplier <= 0:
            raise ValueError("rerank_multiplier must be positive")
        if min_score_threshold < 0:
            raise ValueError("min_score_threshold must be non-negative")
            
        self.vector_db = VectorDatabaseAdapter(vector_db, db_type)
        self.embedder = embedder
        self.use_rerank = use_rerank and reranker_model is not None
        self.rerank_multiplier = rerank_multiplier
        self.min_score_threshold = min_score_threshold
        
        # Initialize re-ranker if needed
        self.reranker: Optional[CrossEncoder] = None
        if self.use_rerank:
            try:
                self.reranker = CrossEncoder(reranker_model)
                logger.info(f"Initialized cross-encoder: {reranker_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize re-ranker {reranker_model}: {e}")
                self.use_rerank = False

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        collection_name: Optional[str] = None,
        include_scores: bool = True,
        return_raw_results: bool = False
    ) -> List[RetrievalResult]:
        """
        Perform the complete retrieval pipeline.

        Args:
            query: User query string
            top_k: Number of final results to return
            collection_name: Vector database collection name (for Chroma-like DBs)
            include_scores: Whether to include similarity scores
            return_raw_results: If True, return raw results without re-ranking
            
        Returns:
            List of RetrievalResult objects sorted by relevance score
            
        Raises:
            ValueError: If query is empty or top_k is invalid
            RuntimeError: If retrieval pipeline fails
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
            
        query = query.strip()
        logger.info(f"Starting retrieval for query: '{query[:50]}...' (top_k={top_k})")
        
        try:
            # Step 1: Embed the query
            query_embeddings = self._embed_query(query)
            # print(query_embeddings)
            # print(f"Retriever Embeddings:{query_embeddings}\n\n\n")
            # Step 2: Determine retrieval count (more if re-ranking)
            retrieval_count = self._calculate_retrieval_count(top_k, return_raw_results)
            

            # Step 3: Vector similarity search
            raw_results = self._vector_search(
                query_embeddings, retrieval_count, collection_name
            )
            

            # Step 4: Filter by minimum score threshold
            filtered_results = self._filter_by_score(raw_results)
            
            if not filtered_results:
                logger.warning("No results passed minimum score threshold")
                return []
            
            # Step 5: Optional re-ranking
            if self.use_rerank and not return_raw_results and len(filtered_results) > 1:
                final_results = self._rerank_results(query, filtered_results, top_k)
            else:
                final_results = self._sort_and_truncate(filtered_results, top_k)
            
            # Step 6: Add ranking information
            for i, result in enumerate(final_results):
                result.rank = i + 1
                
            logger.info(f"Retrieval completed: {len(final_results)} results returned")
            return final_results
            
        except Exception as e:
            logger.error(f"Retrieval pipeline failed: {e}")
            raise RuntimeError(f"Retrieval failed: {e}")

    def _embed_query(self, query: str) -> List[float]:
        """Embed the query text."""
        try:
            # embeddings = self.embedder.embed([query]) #get_embedding
            # print(f" Query : {query}")
            embeddings = self.embedder.get_embedding(query)
            # print(f" Embeddings : {embeddings}")
            if not embeddings:
                raise ValueError("Embedder returned empty results")
            return embeddings
        except Exception as e:
            raise RuntimeError(f"Query embedding failed: {e}")

    def _calculate_retrieval_count(self, top_k: int, return_raw_results: bool) -> int:
        """Calculate how many results to retrieve from vector database."""
        if return_raw_results or not self.use_rerank:
            return top_k
        return max(top_k, int(top_k * self.rerank_multiplier))

    def _vector_search(
        self, 
        query_embedding: List[float], 
        count: int, 
        collection_name: Optional[str]
    ) -> List[RetrievalResult]:
        """Perform vector similarity search."""
        raw_response = self.vector_db.query(
            query_embedding=query_embedding, #query_embedding: Optional[List[float]] = None, 
            top_k=count,
            collection_name=collection_name
        )
        # print(f"Raw Response {raw_response}")

        documents = raw_response.get("documents", [])
        metadatas = raw_response.get("metadatas", [])
        scores = raw_response.get("scores", [])
        
        # Ensure all lists have the same length
        n = len(documents)
        if len(metadatas) != n:
            metadatas = metadatas[:n] + [{}] * (n - len(metadatas))
        if len(scores) != n:
            scores = scores[:n] + [0.0] * (n - len(scores))
            
        return [
            RetrievalResult(
                document=doc,
                metadata=meta,
                score=float(score)
            )
            for doc, meta, score in zip(documents, metadatas, scores)
        ]

    def _filter_by_score(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Filter results by minimum score threshold."""
        if self.min_score_threshold <= 0:
            return results
            
        filtered = [r for r in results if r.score >= self.min_score_threshold]
        if len(filtered) < len(results):
            logger.info(f"Filtered {len(results) - len(filtered)} results below threshold")
        return filtered

    def _rerank_results(
        self, 
        query: str, 
        results: List[RetrievalResult], 
        top_k: int
    ) -> List[RetrievalResult]:
        """Re-rank results using cross-encoder."""
        if not self.reranker:
            return self._sort_and_truncate(results, top_k)
            
        try:
            # Prepare query-document pairs for cross-encoder
            pairs = [[query, result.document] for result in results]
            
            # Get re-ranking scores
            rerank_scores = self.reranker.predict(pairs)
            
            # Update results with new scores
            reranked_results = []
            for result, new_score in zip(results, rerank_scores):
                reranked_result = RetrievalResult(
                    document=result.document,
                    metadata=result.metadata,
                    score=float(new_score)
                )
                reranked_results.append(reranked_result)
            
            # Sort by new scores and return top_k
            reranked_results.sort(key=lambda x: x.score, reverse=True)
            return reranked_results[:top_k]
            
        except Exception as e:
            logger.warning(f"Re-ranking failed, falling back to original scores: {e}")
            return self._sort_and_truncate(results, top_k)

    def _sort_and_truncate(
        self, 
        results: List[RetrievalResult], 
        top_k: int
    ) -> List[RetrievalResult]:
        """Sort results by score and return top_k."""
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        return sorted_results[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics and configuration."""
        return {
            "use_rerank": self.use_rerank,
            "reranker_model": getattr(self.reranker, "config", {}).get("name_or_path", None) if self.reranker else None,
            "rerank_multiplier": self.rerank_multiplier,
            "min_score_threshold": self.min_score_threshold,
            "vector_db_type": self.vector_db.db_type
        }

    def __repr__(self) -> str:
        """String representation of the retriever."""
        reranker_info = f" with {self.reranker}" if self.use_rerank else " (no reranking)"
        return f"EnhancedRetrieverX{reranker_info}"


# Utility functions for common use cases

def create_retriever_from_config(config: Dict[str, Any]) -> EnhancedRetrieverX:
    """
    Create a EnhancedRetrieverX instance from a configuration dictionary.
    
    Args:
        config: Configuration dictionary with keys:
            - vector_db: Vector database instance
            - embedder: Embedder instance  
            - reranker_model: Optional reranker model name
            - use_rerank: Whether to use reranking (default: True)
            - rerank_multiplier: Rerank multiplier (default: 2.0)
            - min_score_threshold: Minimum score threshold (default: 0.0)
            
    Returns:
        Configured EnhancedRetrieverX instance
    """
    required_keys = ["vector_db", "embedder"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required configuration keys: {missing_keys}")
        
    return EnhancedRetrieverX(
        vector_db=config["vector_db"],
        embedder=config["embedder"],
        reranker_model=config.get("reranker_model"),
        use_rerank=config.get("use_rerank", True),
        rerank_multiplier=config.get("rerank_multiplier", 2.0),
        min_score_threshold=config.get("min_score_threshold", 0.0),
        db_type=config.get("db_type", "auto")
    )


def batch_retrieve(
    retriever: EnhancedRetrieverX,
    queries: List[str],
    top_k: int = 10,
    collection_name: Optional[str] = None
) -> List[List[RetrievalResult]]:
    """
    Perform batch retrieval for multiple queries.
    
    Args:
        retriever: EnhancedRetrieverX instance
        queries: List of query strings
        top_k: Number of results per query
        collection_name: Collection name for the vector database
        
    Returns:
        List of result lists, one per query
    """
    results = []
    for query in queries:
        try:
            query_results = retriever.retrieve(
                query=query,
                top_k=top_k,
                collection_name=collection_name
            )
            results.append(query_results)
        except Exception as e:
            logger.error(f"Batch retrieval failed for query '{query[:50]}...': {e}")
            results.append([])
    
    return results


class RetrieverX:
    """
    Two-stage retrieval: vector search + optional cross-encoder re-ranking.

    :param vector_db: any object with a `.query(...)` method
                      Chroma signature: query(collection_name, embedding_vector, top_k, include_metadata=True)
                      FAISS signature: query(embedding_vector, top_k)
    :param embedder: an object with an `.embed([query]) -> [[float]]` method
    :param reranker_model: name of a CrossEncoder model, e.g. "cross-encoder/ms-marco-MiniLM-L-6-v2"
    :param use_rerank: whether to apply cross-encoder re-ranking
    """

    def __init__(
        self,
        vector_db: Any,
        embedder: Any,
        reranker_model,
        use_rerank: bool = True
    ):
        self.vector_db = vector_db
        self.embedder = embedder
        self.use_rerank = use_rerank
        self.reranker: Optional[CrossEncoder] = None
        if self.use_rerank:
            self.reranker = CrossEncoder(reranker_model)

    def retrieve(
        self,
        query: str,
        collection_name: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform retrieval pipeline.

        :param query: user query string
        :param collection_name: vector DB collection to query (ChromaHelper only)
        :param top_k: number of candidates to return (after reranking if enabled)
        :return: list of {"document": str, "metadata": dict, "score": float}
        """
        # 1) embed the query
        q_emb = self.embedder.embed([query])[0]

        # 2) initial vector DB retrieval
        try:
            if collection_name == None:
                 # Fallback to FAISSHelper signature
                hits = self.vector_db.query(q_emb, top_k * (2 if self.use_rerank else 1))
                docs   = [h.get("text", "")     for h in hits]
                metas  = [h.get("metadata", {}) for h in hits]
                scores = [0.0 for _ in hits]
                res = {"documents": docs, "metadatas": metas, "scores": scores}
                
            else:
               # Try Chroma-like signature
                res = self.vector_db.query(
                    collection_name=collection_name,
                    query_embedding=q_emb,
                    top_k=top_k * (2 if self.use_rerank else 1),
                    include_metadata=True
                ) 

        except TypeError as e:
           raise RuntimeError(f"[❌ ERROR] Unexpected Error during retrieval : {e}")

        if not isinstance(res, dict):
            raise RuntimeError(f"[❌ ERROR] Vector DB returned invalid response: {res!r}")

        # 3) normalize fields
        docs   = res.get("documents") or []
        metas  = res.get("metadatas") or []
        scores = res.get("distances", res.get("scores", None))

        n = len(docs)
        if len(metas) != n:
            metas = [{}] * n
        if not isinstance(scores, list) or len(scores) != n:
            scores = [0.0] * n

        candidates: List[Tuple[str, Dict[str, Any], float]] = list(zip(docs, metas, scores))

        # 4) optional re-ranking
        if self.use_rerank and self.reranker:
            pairs = [[query, doc] for doc, _, _ in candidates]
            rerank_scores = self.reranker.predict(pairs)
            reranked = sorted(
                zip(candidates, rerank_scores),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]
            return [
                {"document": doc, "metadata": meta, "score": float(r_score)}
                for ((doc, meta, _), r_score) in reranked
            ]

        # 5) no rerank: return top_k by original score
        sorted_orig = sorted(candidates, key=lambda x: x[2], reverse=True)[:top_k]
        return [
            {"document": doc, "metadata": meta, "score": float(score)}
            for doc, meta, score in sorted_orig
        ]


# # langxchange/EnhancedRetrieverX.py

# from typing import List, Dict, Any, Optional, Tuple
# from sentence_transformers import CrossEncoder


# class RetrieverX:
#     """
#     Two-stage retrieval: vector search + optional cross-encoder re-ranking.

#     :param vector_db: any object with a `.query(collection_name, embedding_vector, top_k, include_metadata=True)` method
#                       returning a dict with keys "documents" (List[str]), optionally "metadatas", "distances" or "scores".
#     :param embedder: an object with an `.embed([query]) -> [[float]]` method
#     :param reranker_model: name of a CrossEncoder model, e.g. "cross-encoder/ms-marco-MiniLM-L-6-v2"
#     :param use_rerank: whether to apply cross-encoder re-ranking
#     """

#     def __init__(
#         self,
#         vector_db: Any,
#         embedder: Any,
#         reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
#         use_rerank: bool = True
#     ):
#         self.vector_db = vector_db
#         self.embedder = embedder
#         self.use_rerank = use_rerank
#         self.reranker: Optional[CrossEncoder] = None
#         if self.use_rerank:
#             self.reranker = CrossEncoder(reranker_model)

#     def retrieve(
#         self,
#         query: str,
#         collection_name: str,
#         top_k: int = 10
#     ) -> List[Dict[str, Any]]:
#         """
#         Perform retrieval pipeline.

#         :param query: user query string
#         :param collection_name: vector DB collection to query
#         :param top_k: number of candidates to return (after reranking if enabled)
#         :return: list of {"document": str, "metadata": dict, "score": float}
#         """
#         # 1) embed the query
#         q_emb = self.embedder.embed([query])[0]

#         # 2) initial vector DB retrieval
#         res = self.vector_db.query(
#             collection_name=collection_name,
#             embedding_vector=q_emb,
#             top_k=top_k * (2 if self.use_rerank else 1),
#             include_metadata=True
#         )
#         #return res
#         if not isinstance(res, dict):
#             raise RuntimeError(f"[❌ ERROR] Vector DB returned invalid response: {res!r}")

#         docs   = res.get("documents") or []
#         metas  = res.get("metadatas") or []
#         scores = res.get("distances", res.get("scores", None))

#         n = len(docs)
#         if len(metas) != n:
#             metas = [{}] * n
#         if not isinstance(scores, list) or len(scores) != n:
#             scores = [0.0] * n

#         candidates: List[Tuple[str, Dict[str, Any], float]] = list(zip(docs, metas, scores))

#         # 3) optional re-ranking
#         # if self.use_rerank and self.reranker:
#         #     pairs = [[query, doc] for doc, _, _ in candidates]
#         #     rerank_scores = self.reranker.predict(pairs)
#         #     reranked = sorted(
#         #         zip(candidates, rerank_scores),
#         #         key=lambda x: x[1],
#         #         reverse=True
#         #     )[:top_k]
#         #     return [
#         #         {"document": doc, "metadata": meta, "score": float(r_score)}
#         #         for ((doc, meta, _), r_score) in reranked
#         #     ]

#         # 4) no rerank: return top_k by original score
#         sorted_orig = sorted(candidates, key=lambda x: x[2], reverse=True)[:top_k]
#         return [
#             {"document": doc, "metadata": meta, "score": float(score)}
#             for doc, meta, score in sorted_orig
#         ]
