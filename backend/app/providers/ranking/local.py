from collections.abc import Sequence
from typing import Any
from sentence_transformers import CrossEncoder
from app.providers.ranking.base import BaseRankingProvider
from app.core.config.config import settings

class LocalRankingProvider(BaseRankingProvider):
    """
    Sentence-Transformers local CPU cross-encoder reranking provider.
    Reranks candidates against job description specifications offline.
    """
    def __init__(self, model_name: str | None = None):
        # We can default to setting or "BAAI/bge-reranker-base"
        self.model_name = model_name or getattr(settings, "RERANK_MODEL", "BAAI/bge-reranker-base")
        self._model = None

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(self.model_name, device="cpu")
        return self._model

    async def rerank(
        self,
        query: str,
        documents: Sequence[dict[str, Any]],
        limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Re-evaluate candidates against recruiter query using BAAI/bge-reranker-base model.
        """
        if not documents:
            return []

        # Prepare pairs for cross-encoder prediction
        pairs = []
        for doc in documents:
            # We look for a dedicated "text" key or construct it from summaries/skills
            text = doc.get("text") or doc.get("professional_summary") or ""
            if not text and "skills" in doc:
                text = f"Skills: {', '.join(doc['skills'])}"
            pairs.append([query, text])

        # Predict scores
        scores = self.model.predict(pairs)
        
        # Convert to standard Python float and attach to candidate document
        results = []
        for doc, score in zip(documents, scores):
            doc_copy = dict(doc)
            doc_copy["rerank_score"] = float(score)
            results.append(doc_copy)

        # Sort descending by rerank score
        sorted_results = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
        if limit:
            sorted_results = sorted_results[:limit]
            
        return sorted_results
