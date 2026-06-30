import pytest
from app.providers.embedding.local import LocalEmbeddingProvider
from app.core.config.config import settings

@pytest.mark.asyncio
async def test_local_embedding_provider():
    """
    Test that LocalEmbeddingProvider loads sentence-transformers and embeds
    queries and batches of documents with correct dimensions.
    """
    provider = LocalEmbeddingProvider()
    
    # 1. Embed query
    query = "Java Software Engineer"
    q_vec = await provider.embed_query(query)
    
    assert isinstance(q_vec, list)
    assert len(q_vec) == settings.EMBEDDING_DIMENSION
    assert all(isinstance(x, float) for x in q_vec)
    
    # 2. Embed batch of documents
    docs = ["Python developer with ML expertise", "Cloud solutions architect"]
    doc_vecs = await provider.embed_documents(docs)
    
    assert isinstance(doc_vecs, list)
    assert len(doc_vecs) == 2
    assert len(doc_vecs[0]) == settings.EMBEDDING_DIMENSION
    assert len(doc_vecs[1]) == settings.EMBEDDING_DIMENSION
