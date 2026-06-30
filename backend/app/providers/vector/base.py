from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

class BaseVectorProvider(ABC):
    """
    Abstract interface wrapping vector storage CRUD and indexing commands.
    """
    @abstractmethod
    async def upsert(
        self,
        collection_name: str,
        ids: Sequence[str],
        embeddings: Sequence[list[float]],
        payloads: Sequence[dict[str, Any]]
    ) -> bool:
        """
        Write or update vector coordinates and context payloads inside a collection.
        """
        pass

    @abstractmethod
    async def query(
        self,
        collection_name: str,
        query_embedding: list[float],
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieve candidate entities closest to a high-dimensional search coordinates.
        """
        pass

    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """
        Create a vector indexing namespace / catalog with specific dimensions.
        """
        pass
