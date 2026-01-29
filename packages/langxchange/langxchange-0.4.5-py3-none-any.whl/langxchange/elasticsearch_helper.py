import uuid
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm
from elasticsearch import Elasticsearch

@dataclass
class ElasticsearchConfig:
    host: str = "http://localhost:9200"
    index_prefix: str = ""
    embedding_dim: int = 1536
    batch_size: int = 100
    max_workers: int = 8
    progress_bar: bool = True
    refresh_on_insert: bool = False


class ElasticsearchHelperError(Exception):
    pass


class EnhancedElasticsearchHelper:
    """
    Elasticsearch vector helper with Chroma/Milvus parity
    """

    def __init__(
        self,
        llm_helper: Any,
        config: Optional[ElasticsearchConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        if not llm_helper or not hasattr(llm_helper, "get_embedding"):
            raise ElasticsearchHelperError(
                "llm_helper with get_embedding() required"
            )

        self.llm_helper = llm_helper
        self.config = config or ElasticsearchConfig()
        self.logger = logger or self._setup_logger()

        try:
            self.client = Elasticsearch(self.config.host)
            self.client.info()
            self.logger.info("✅ Connected to Elasticsearch")
        except Exception as e:
            raise ElasticsearchHelperError(f"Failed to connect to Elasticsearch: {e}")

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("elasticsearch_helper")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


    def create_collection(self, index_name: str) -> str:
        index_name = f"{self.config.index_prefix}{index_name}"

        if self.client.indices.exists(index=index_name):
            return index_name

        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "document": {"type": "text"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": self.config.embedding_dim,
                        "index": True,
                        "similarity": "cosine"
                    },
                    "metadata": {"type": "object", "enabled": True}
                }
            }
        }

        try:
            self.client.indices.create(index=index_name, **mapping)
            self.logger.info(f"📦 Created index '{index_name}'")
            return index_name
        except Exception as e:
            raise ElasticsearchHelperError(f"Index creation failed: {e}")


    def _validate_embeddings(self, embeddings: List[List[float]]) -> bool:
        return all(
            isinstance(e, (list, tuple))
            and len(e) == self.config.embedding_dim
            for e in embeddings
        )

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = [self.llm_helper.get_embedding(t) for t in texts]
            if not self._validate_embeddings(embeddings):
                raise ValueError("Invalid embeddings")
            return embeddings
        except Exception as e:
            raise ElasticsearchHelperError(f"Embedding failure: {e}")

    def insert_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None,
        ids: Optional[List[str]] = None,
        generate_embeddings: bool = True
    ) -> List[str]:

        if not documents:
            return []

        index = self.create_collection(collection_name)

        ids = ids or [str(uuid.uuid4()) for _ in documents]
        metadatas = metadatas or [{} for _ in documents]

        if embeddings is None and generate_embeddings:
            embeddings = self.get_embeddings_batch(documents)

        if not self._validate_embeddings(embeddings):
            raise ElasticsearchHelperError("Invalid embeddings")

        actions = []
        for i in range(len(documents)):
            actions.append({
                "_index": index,
                "_id": ids[i],
                "_source": {
                    "id": ids[i],
                    "document": documents[i],
                    "embedding": embeddings[i],
                    "metadata": metadatas[i]
                }
            })

        try:
            for action in actions:
                self.client.index(
                    index=index,
                    id=action["_id"],
                    document=action["_source"],
                    refresh=self.config.refresh_on_insert
                )
            return ids
        except Exception as e:
            raise ElasticsearchHelperError(f"Insert failed: {e}")


    def ingest_dataframe(
        self,
        df: pd.DataFrame,
        collection_name: str,
        document_column: str = "documents",
        metadata_columns: Optional[List[str]] = None
    ) -> int:

        if df.empty:
            return 0

        batches = [
            df[i:i + self.config.batch_size]
            for i in range(0, len(df), self.config.batch_size)
        ]

        def process_batch(batch: pd.DataFrame) -> int:
            docs = batch[document_column].tolist()
            metadatas = (
                batch[metadata_columns].to_dict("records")
                if metadata_columns else [{} for _ in docs]
            )
            self.insert_documents(
                collection_name=collection_name,
                documents=docs,
                metadatas=metadatas
            )
            return len(docs)

        processed = 0
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as ex:
            futures = [ex.submit(process_batch, b) for b in batches]

            if self.config.progress_bar:
                with tqdm(total=len(batches), desc="🔄 Ingesting") as pbar:
                    for f in as_completed(futures):
                        processed += f.result()
                        pbar.update(1)
            else:
                for f in as_completed(futures):
                    processed += f.result()

        return processed


    def query(
        self,
        collection_name: str,
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        if not query_embedding:
            if not query_text:
                raise ElasticsearchHelperError("query_text or query_embedding required")
            query_embedding = self.llm_helper.get_embedding(query_text)

        index = self.create_collection(collection_name)

        query = {
            "size": top_k,
            "query": {
                "script_score": {
                    "query": {
                        "bool": {
                            "filter": [
                                {"term": {f"metadata.{k}": v}}
                                for k, v in (where_filter or {}).items()
                            ]
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.q, 'embedding') + 1.0",
                        "params": {"q": query_embedding}
                    }
                }
            }
        }

        try:
            return self.client.search(index=index, body=query)
        except Exception as e:
            raise ElasticsearchHelperError(f"Query failed: {e}")

    def get_collection_count(self, collection_name: str) -> int:
        index = self.create_collection(collection_name)
        return self.client.count(index=index)["count"]

    def delete_collection(self, collection_name: str) -> bool:
        index = f"{self.config.index_prefix}{collection_name}"
        self.client.indices.delete(index=index, ignore=[404])
        return True

    def list_collections(self) -> List[str]:
        return list(self.client.indices.get_alias("*").keys())
