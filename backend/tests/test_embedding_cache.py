import pytest
from app.services.embedding_service import EmbeddingService

@pytest.mark.asyncio
async def test_embedding_cache_operations(tmp_path):
    """
    Test persistent SQLite cache hits, misses, invalidation, and clear.
    """
    import os
    # Temporarily override settings config cache dir
    cache_service = EmbeddingService()
    # Direct database path update for testing isolation
    test_db = os.path.join(tmp_path, "test_cache.db")
    cache_service.db_path = test_db
    cache_service._init_db()
    
    cand_id = "test_candidate_01"
    e_type = "skills"
    p_hash = "abc123hash"
    vec = [0.1, 0.2, 0.3]
    
    # 1. Initially cache should return None (miss)
    cached = await cache_service.get_cached_embedding(cand_id, e_type, p_hash)
    assert cached is None
    
    # 2. Write to cache
    await cache_service.cache_embedding(cand_id, e_type, p_hash, vec)
    
    # 3. Retrieve from cache with correct hash (hit)
    hit = await cache_service.get_cached_embedding(cand_id, e_type, p_hash)
    assert hit == vec
    
    # 4. Retrieve from cache with modified hash (miss / invalidation)
    miss = await cache_service.get_cached_embedding(cand_id, e_type, "differenthash")
    assert miss is None
    
    # 5. Clear cache
    cache_service.clear_cache()
    cleared = await cache_service.get_cached_embedding(cand_id, e_type, p_hash)
    assert cleared is None
