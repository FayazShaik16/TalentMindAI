from abc import ABC, abstractmethod
from collections.abc import Sequence

class BaseEmbeddingProvider(ABC):
    """
    Abstract interface for generating vector embeddings from text strings.
    """
    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """
        Generate embedding vector representing a single text query.
        """
        pass

    @abstractmethod
    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generate a batch of embedding vectors representing document texts.
        """
        pass
