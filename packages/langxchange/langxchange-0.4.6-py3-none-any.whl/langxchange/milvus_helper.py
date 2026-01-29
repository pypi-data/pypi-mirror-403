import uuid
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from tqdm import tqdm

from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)

@dataclass
class MilvusConfig:
    host: str = "localhost"
    port: str = "19530"
    api_key: Optional[str] = None
    collection_prefix: str = ""
    embedding_dim: int = 1536
    batch_size: int = 100
    max_workers: int = 8
    progress_bar: bool = True


class MilvusHelperError(Exception):
    pass


class EnhancedMilvusHelper:
    """
    Production-grade Milvus helper inspired by EnhancedChromaHelper
    """

    def __init__(
        self,
        llm_helper: Any,
        config: Optional[MilvusConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        if not llm_helper or not hasattr(llm_helper, "get_embedding"):
            raise MilvusHelperError(
                "llm_helper with get_embedding() is required"
            )

        self.llm_helper = llm_helper
        self.config = config or MilvusConfig()
        self.logger = logger or self._setup_logger()

        try:
            conn_params = {
                "alias": "default",
                "host": self.config.host,
                "port": self.config.port
            }
            if self.config.api_key:
                conn_params["token"] = self.config.api_key
                
            connections.connect(**conn_params)
            self.logger.info("✅ Connected to Milvus")
        except Exception as e:
            raise MilvusHelperError(f"Failed to connect to Milvus: {e}")


    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("milvus_helper")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger


    def create_collection(self, name: str) -> Collection:
        name = f"{self.config.collection_prefix}{name}"

        if utility.has_collection(name):
            return Collection(name)

        schema = CollectionSchema(
            fields=[
                FieldSchema(
                    name="id",
                    dtype=DataType.VARCHAR,
                    is_primary=True,
                    max_length=64
                ),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.config.embedding_dim
                ),
                FieldSchema(
                    name="document",
                    dtype=DataType.VARCHAR,
                    max_length=65535
                ),
                FieldSchema(
                    name="metadata",
                    dtype=DataType.JSON
                ),
            ],
            description="Enhanced Milvus Collection"
        )

        collection = Collection(name=name, schema=schema)

        collection.create_index(
            field_name="embedding",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 8, "efConstruction": 64}
            }
        )

        collection.load()
        self.logger.info(f"📦 Created collection '{name}'")
        return collection

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
            raise MilvusHelperError(f"Embedding failure: {e}")

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

        collection = self.create_collection(collection_name)

        ids = ids or [str(uuid.uuid4()) for _ in documents]
        metadatas = metadatas or [{} for _ in documents]

        if embeddings is None and generate_embeddings:
            embeddings = self.get_embeddings_batch(documents)

        if not self._validate_embeddings(embeddings):
            raise MilvusHelperError("Invalid embeddings supplied")

        data = [
            ids,
            embeddings,
            documents,
            metadatas
        ]

        try:
            collection.insert(data)
            collection.flush()
            return ids
        except Exception as e:
            raise MilvusHelperError(f"Insert failed: {e}")


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
                collection_name,
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
        where_filter: Optional[str] = None
    ) -> Dict[str, Any]:

        if not query_embedding:
            if not query_text:
                raise MilvusHelperError("query_text or query_embedding required")
            query_embedding = self.llm_helper.get_embedding(query_text)

        collection = self.create_collection(collection_name)
        collection.load()

        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=top_k,
            expr=where_filter,
            output_fields=["document", "metadata"]
        )

        return results

    def get_collection_count(self, collection_name: str) -> int:
        collection = self.create_collection(collection_name)
        return collection.num_entities

    def delete_collection(self, collection_name: str) -> bool:
        utility.drop_collection(collection_name)
        return True

    def list_collections(self) -> List[str]:
        return utility.list_collections()
