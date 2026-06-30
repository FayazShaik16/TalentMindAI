from collections.abc import Sequence
from app.providers.embedding.base import BaseEmbeddingProvider

class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """
    Interface skeleton for future Ollama embedding endpoint integration.
    """
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name

    async def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("OllamaEmbeddingProvider is not implemented yet.")

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        raise NotImplementedError("OllamaEmbeddingProvider is not implemented yet.")
