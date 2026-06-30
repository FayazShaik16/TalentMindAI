from collections.abc import Sequence
from sentence_transformers import SentenceTransformer
from app.providers.embedding.base import BaseEmbeddingProvider
from app.core.config.config import settings

class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Sentence-Transformers local CPU execution provider.
    Loads and runs transformer embeddings offline.
    """
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name, device="cpu")
        return self._model

    async def embed_query(self, text: str) -> list[float]:
        """
        Generate embedding vector representing a single text query.
        """
        if not text:
            return [0.0] * settings.EMBEDDING_DIMENSION
        vector = self.model.encode(text, normalize_embeddings=True)
        return [float(x) for x in vector]

    async def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """
        Generate a batch of embedding vectors representing document texts.
        """
        if not texts:
            return []
        vectors = self.model.encode(list(texts), normalize_embeddings=True)
        return [[float(x) for x in vec] for vec in vectors]
