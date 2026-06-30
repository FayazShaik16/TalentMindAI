from collections.abc import Sequence
from typing import Any
from app.providers.vector.base import BaseVectorProvider

class MilvusProvider(BaseVectorProvider):
    """
    Interface skeleton for future Milvus Vector Store integration.
    """
    def __init__(self, index_dir: str | None = None):
        pass

    async def upsert(
        self,
        collection_name: str,
        ids: Sequence[str],
        embeddings: Sequence[list[float]],
        payloads: Sequence[dict[str, Any]]
    ) -> bool:
        raise NotImplementedError("MilvusProvider is not implemented yet.")

    async def query(
        self,
        collection_name: str,
        query_embedding: list[float],
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("MilvusProvider is not implemented yet.")

    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        raise NotImplementedError("MilvusProvider is not implemented yet.")
