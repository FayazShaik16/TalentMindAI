from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

class BaseRankingProvider(ABC):
    """
    Abstract interface wrapping candidates relevance reranking pipelines.
    """
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: Sequence[dict[str, Any]],
        limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Re-evaluate raw retrieve candidate nodes against target specifications.
        """
        pass
