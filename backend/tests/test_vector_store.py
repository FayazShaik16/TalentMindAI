import os
import pytest
from app.providers.vector.faiss import FAISSProvider
from app.core.config.config import settings

@pytest.mark.asyncio
async def test_faiss_provider_lifecycle(tmp_path):
    """
    Test creating a collection, upserting vectors, querying, and checking stats.
    """
    # Instantiate provider targeting a temp directory
    provider = FAISSProvider(index_dir=str(tmp_path))
    col = "test_col"
    dim = 4
    
    # 1. Create collection
    success = await provider.create_collection(col, dim)
    assert success is True
    
    # Check that files were created
    index_path, db_path = provider._get_paths(col)
    assert os.path.exists(index_path)
    assert os.path.exists(db_path)
    
    # 2. Upsert vectors
    ids = ["cand_a", "cand_b"]
    embeddings = [
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8]
    ]
    payloads = [
        {"location": "Boston", "years_experience": 2.0},
        {"location": "Seattle", "years_experience": 5.0}
    ]
    
    success_upsert = await provider.upsert(col, ids, embeddings, payloads)
    assert success_upsert is True
    
    # 3. Query closest vectors (L2 or Cosine distance)
    # Cosine/dot will prioritize closer matches
    results = await provider.query(col, [0.1, 0.2, 0.3, 0.4], limit=2)
    assert len(results) == 2
    assert results[0]["candidate_id"] == "cand_a"
    
    # 4. Get Statistics
    stats = await provider.get_statistics(col)
    assert stats["ntotal"] == 2
    assert stats["dimension"] == dim
    
    # 5. Query with metadata filtering (location match)
    results_filtered = await provider.query(
        col, [0.1, 0.2, 0.3, 0.4], limit=2,
        filter_metadata={"location": "Seattle"}
    )
    assert len(results_filtered) == 1
    assert results_filtered[0]["candidate_id"] == "cand_b"
    
    # 6. Clear collection
    await provider.clear_collection(col)
    assert not os.path.exists(index_path)
    assert not os.path.exists(db_path)
