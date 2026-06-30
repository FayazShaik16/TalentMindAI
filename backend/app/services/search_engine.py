import time
from typing import Any
from app.core.config.config import settings
from app.core.logging.logging import logger
from app.providers.vector.faiss import FAISSProvider
from app.services.embedding_service import embedding_service

class SearchEngine:
    """
    Semantic Intelligence Similarity Search Engine.
    Executes dense retrieval, pre-reranking metadata filtering,
    and produces execution traces for audit/observability.
    """
    def __init__(self):
        self.vector_provider = FAISSProvider()

    async def search(
        self,
        query: str,
        collection_name: str = "summary",
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Runs vector query retrieval followed by metadata constraints matching.
        Produces full AI Trace maps.
        """
        start_time = time.perf_counter()

        # Step 1: Generate recruiter intent query embedding
        emb_start = time.perf_counter()
        query_vector = await embedding_service.embed_recruiter_query(query)
        embedding_duration = time.perf_counter() - emb_start

        # Step 2: Dense retrieval via vector provider
        search_start = time.perf_counter()
        raw_results = await self.vector_provider.query(
            collection_name=collection_name,
            query_embedding=query_vector,
            limit=limit,
            filter_metadata=filter_metadata
        )
        search_duration = time.perf_counter() - search_start

        total_duration = time.perf_counter() - start_time

        # Step 3: Compile AI Trace Map
        # Traces are critical observability records for future explainability engines
        trace = {
            "recruiter_query": query,
            "embedding_model": settings.EMBEDDING_MODEL,
            "collection": collection_name,
            "vector_search_metric": settings.VECTOR_METRIC,
            "vector_index_type": settings.VECTOR_INDEX_TYPE,
            "timing_logs": {
                "embedding_generation_sec": round(embedding_duration, 4),
                "vector_lookup_sec": round(search_duration, 4),
                "total_execution_sec": round(total_duration, 4),
            },
            "filters_applied": filter_metadata or {},
            "candidates_evaluated_count": len(raw_results),
            "execution_steps": [
                "Recruiter Query Received",
                "Text Query Vectorized on CPU via sentence-transformers",
                f"FAISS dense vector index scan on metric: {settings.VECTOR_METRIC}",
                "SQLite candidate metadata pre-filter joins executed",
                "Results compiled into similarity rank order"
            ]
        }

        # Structured response
        output = {
            "results": raw_results,
            "trace": trace
        }

        logger.info(
            "semantic_search_executed",
            query=query,
            collection=collection_name,
            hits=len(raw_results),
            total_sec=round(total_duration, 4)
        )
        return output

    async def hybrid_search_mock(
        self,
        query: str,
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Architecture preparation placeholder for future hybrid retrieval
        (combining keyword search, vector search, and behavioral scoring).
        """
        # Under hybrid preparation, we return semantic retrieval results
        # indicating that keyword matches are pending integration in Phase 2
        semantic_out = await self.search(query, "summary", limit, filter_metadata)
        semantic_out["trace"]["execution_steps"].append(
            "Hybrid retrieval warning: Keyword / Behavioral indexes are currently bypassed (Phase 2 feature)"
        )
        return semantic_out

search_engine = SearchEngine()
