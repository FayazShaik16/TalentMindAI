import os
import json
import sqlite3
import threading
import asyncio
from collections.abc import Sequence
from typing import Any
import numpy as np
import faiss

from app.providers.vector.base import BaseVectorProvider
from app.core.config.config import settings
from app.core.logging.logging import logger

class FAISSProvider(BaseVectorProvider):
    """
    FAISS CPU Vector Store Provider.
    Manages high-dimensional vector indices and runs in-memory/metadata queries.
    Uses SQLite to persist metadata mapping integer index offsets to candidate IDs.
    """
    def __init__(self, index_dir: str | None = None):
        self.index_dir = index_dir or settings.VECTOR_INDEX_PATH
        os.makedirs(self.index_dir, exist_ok=True)
        self._lock = threading.Lock()

    def _get_paths(self, collection_name: str) -> tuple[str, str]:
        index_path = os.path.join(self.index_dir, f"{collection_name}.index")
        db_path = os.path.join(self.index_dir, f"{collection_name}_metadata.db")
        return index_path, db_path

    def _init_db(self, db_path: str):
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mapping (
                    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Index for fast filtering & queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_candidate_id ON mapping(candidate_id)")
            conn.commit()
        finally:
            conn.close()

    def _get_faiss_metric(self) -> int:
        metric_str = settings.VECTOR_METRIC.lower()
        if metric_str in ["cosine", "dot"]:
            return faiss.METRIC_INNER_PRODUCT
        return faiss.METRIC_L2

    def _create_faiss_index(self, dimension: int) -> faiss.Index:
        idx_type = settings.VECTOR_INDEX_TYPE.lower()
        metric = self._get_faiss_metric()

        if idx_type == "hnsw":
            # HNSW Flat index with 32 connections per node
            return faiss.IndexHNSWFlat(dimension, 32, metric)
        elif idx_type == "ivf":
            # Simple IVF Flat index with 100 centroids
            quantizer = faiss.IndexFlat(dimension, metric)
            # Default to Flat quantizer, nlist=100 centroids
            # Note: IVF requires training, so we will wrap it with IndexIVFFlat
            # For simplicity under small testing constraints, Flat quantizer is initialized
            nlist = min(100, dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist, metric)
            # Set direct training fallback
            index.make_direct_map()
            return index
        elif idx_type == "pq":
            # Product Quantization index
            return faiss.IndexPQ(dimension, 8, 8, metric)
        else:
            # Default to Flat index
            if metric == faiss.METRIC_INNER_PRODUCT:
                return faiss.IndexFlatIP(dimension)
            return faiss.IndexFlatL2(dimension)

    def _load_index(self, index_path: str, dimension: int) -> faiss.Index:
        if os.path.exists(index_path):
            try:
                return faiss.read_index(index_path)
            except Exception as e:
                logger.error("faiss_load_index_failed", path=index_path, error=str(e))
        
        # Fallback to creating a new index
        logger.info("creating_new_faiss_index", path=index_path, dimension=dimension)
        return self._create_faiss_index(dimension)

    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """
        Creates metadata db and empty FAISS index files.
        """
        def _sync_create():
            with self._lock:
                index_path, db_path = self._get_paths(collection_name)
                self._init_db(db_path)
                index = self._create_faiss_index(dimension)
                faiss.write_index(index, index_path)
                return True
        return await asyncio.to_thread(_sync_create)

    async def upsert(
        self,
        collection_name: str,
        ids: Sequence[str],
        embeddings: Sequence[list[float]],
        payloads: Sequence[dict[str, Any]]
    ) -> bool:
        """
        Appends vectors to FAISS index and inserts metadata into SQLite companion mapping.
        """
        if not ids:
            return True

        def _sync_upsert():
            with self._lock:
                index_path, db_path = self._get_paths(collection_name)
                self._init_db(db_path)

                dimension = len(embeddings[0])
                index = self._load_index(index_path, dimension)

                # Normalize vectors for Cosine Similarity (Inner Product)
                vectors_np = np.array(embeddings, dtype=np.float32)
                if settings.VECTOR_METRIC.lower() in ["cosine", "dot"]:
                    norms = np.linalg.norm(vectors_np, axis=1, keepdims=True)
                    # Avoid division by zero
                    norms = np.where(norms == 0, 1.0, norms)
                    vectors_np = vectors_np / norms

                # Train if needed (IVF or PQ)
                if not index.is_trained:
                    logger.info("training_faiss_index", collection=collection_name, count=len(vectors_np))
                    index.train(vectors_np)

                # Append to FAISS
                index.add(vectors_np)
                faiss.write_index(index, index_path)

                # Append to SQLite mappings
                conn = sqlite3.connect(db_path)
                try:
                    cursor = conn.cursor()
                    for c_id, payload in zip(ids, payloads):
                        cursor.execute(
                            "INSERT INTO mapping (candidate_id, payload) VALUES (?, ?)",
                            (c_id, json.dumps(payload))
                        )
                    conn.commit()
                finally:
                    conn.close()


                logger.info(
                    "faiss_upsert_completed",
                    collection=collection_name,
                    inserted_count=len(ids),
                    total_count=index.ntotal
                )
                return True

        return await asyncio.to_thread(_sync_upsert)

    async def query(
        self,
        collection_name: str,
        query_embedding: list[float],
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Queries FAISS and SQLite for nearest candidates, applying pre-reranking filters.
        """
        def _sync_query():
            with self._lock:
                index_path, db_path = self._get_paths(collection_name)
                if not os.path.exists(index_path) or not os.path.exists(db_path):
                    return []

                dimension = len(query_embedding)
                index = faiss.read_index(index_path)
                if index.ntotal == 0:
                    return []

                # Normalize query embedding for cosine
                query_np = np.array([query_embedding], dtype=np.float32)
                if settings.VECTOR_METRIC.lower() in ["cosine", "dot"]:
                    norm = np.linalg.norm(query_np)
                    if norm > 0:
                        query_np = query_np / norm

                # Retrieve more candidate IDs from vector search than the requested limit
                # to allow margin for in-memory metadata filtering.
                search_k = min(index.ntotal, max(limit * 5, settings.TOP_K_DEFAULT))
                distances, indices = index.search(query_np, search_k)

                scores = distances[0]
                row_ids = indices[0]

                results = []
                seen_candidates = set()

                # Open SQLite mapping db
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                try:
                    for score, r_id in zip(scores, row_ids):
                        if r_id == -1:
                            continue
                        
                        # FAISS row index is 0-indexed offset.
                        # SQLite row_id table is AUTOINCREMENT (1-indexed starting at 1).
                        sqlite_row_id = int(r_id) + 1

                        cursor = conn.execute(
                            "SELECT candidate_id, payload FROM mapping WHERE row_id = ?",
                            (sqlite_row_id,)
                        )
                        row = cursor.fetchone()
                        if not row:
                            continue

                        cand_id = row["candidate_id"]

                        # Skip older duplicates of the same candidate (keep nearest score match)
                        if cand_id in seen_candidates:
                            continue

                        payload = json.loads(row["payload"])
                        
                        # Metadata Filtering
                        if filter_metadata:
                            match = True
                            for f_key, f_val in filter_metadata.items():
                                # Match criteria
                                p_val = payload.get(f_key)
                                if isinstance(f_val, list):
                                    # List condition (e.g. skills filter matches at least one candidate skill)
                                    if not p_val or not any(x.lower() in [s.lower() for s in p_val] for x in f_val):
                                        match = False
                                        break
                                elif f_key == "years_experience":
                                    # Numerical bounds check
                                    if p_val is None or float(p_val) < float(f_val):
                                        match = False
                                        break
                                else:
                                    # String match (case insensitive)
                                    if not p_val or str(p_val).strip().lower() != str(f_val).strip().lower():
                                        match = False
                                        break
                            if not match:
                                continue

                        seen_candidates.add(cand_id)
                        results.append({
                            "candidate_id": cand_id,
                            "score": float(score),
                            "payload": payload
                        })

                        if len(results) >= limit:
                            break
                finally:
                    conn.close()

                return results

        return await asyncio.to_thread(_sync_query)

    async def get_statistics(self, collection_name: str) -> dict:
        """
        Returns stats about a FAISS index collection.
        """
        index_path, db_path = self._get_paths(collection_name)
        if not os.path.exists(index_path):
            return {"status": "collection_not_found"}

        with self._lock:
            index = faiss.read_index(index_path)
            return {
                "ntotal": index.ntotal,
                "dimension": index.d,
                "is_trained": index.is_trained,
                "metric_type": settings.VECTOR_METRIC,
                "index_type": settings.VECTOR_INDEX_TYPE
            }

    async def clear_collection(self, collection_name: str) -> bool:
        """
        Deletes vector index files and database mappings for a collection.
        """
        index_path, db_path = self._get_paths(collection_name)
        with self._lock:
            if os.path.exists(index_path):
                os.remove(index_path)
            if os.path.exists(db_path):
                os.remove(db_path)
            return True
