import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.candidate import Candidate
from app.database.repositories.candidate import CandidateRepository
from app.schemas.candidate import CandidateProfile, PersonalInfo
from tests.test_pipeline import clear_db
from app.providers.vector.faiss import FAISSProvider

@pytest.mark.asyncio
async def test_semantic_api_endpoints(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that all API routes exposed under /api/v1/semantic function correctly.
    """
    await clear_db(db_session)
    provider = FAISSProvider()
    for col in ["summary", "career", "projects", "skills", "education"]:
        await provider.clear_collection(col)

    # 1. Insert a mock candidate into DB
    profile = CandidateProfile(
        id="api_search_01",
        personal_info=PersonalInfo(
            first_name="Jane",
            last_name="Searcher",
            email="jane.search@example.com",
            location="Boston"
        ),
        experiences=[],
        projects=[],
        educations=[],
        skills=[]
    )
    repo = CandidateRepository(db_session)
    await repo.upsert_candidate_profile(profile)
    await db_session.commit()

    # 2. Get list of models
    models_res = await client.get("/api/v1/semantic/embeddings/models")
    assert models_res.status_code == 200
    models_data = models_res.json()
    assert models_data["success"] is True
    assert "supported_models" in models_data["data"]

    # 3. Check status
    status_res = await client.get("/api/v1/semantic/embeddings/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["success"] is True
    assert status_data["data"]["active_model"] == "BAAI/bge-base-en-v1.5"

    # 4. Build embeddings
    build_res = await client.post("/api/v1/semantic/embeddings/build")
    assert build_res.status_code == 200
    build_data = build_res.json()
    assert build_data["success"] is True
    assert build_data["data"]["processed_count"] == 1

    # 5. Search
    search_payload = {
        "query": "Looking for Jane in Boston",
        "collection": "summary",
        "limit": 5,
        "filter_metadata": {"location": "Boston"}
    }
    search_res = await client.post("/api/v1/semantic/search", json=search_payload)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["success"] is True
    assert len(search_data["data"]["results"]) == 1
    assert search_data["data"]["results"][0]["candidate_id"] == "api_search_01"

    # 6. Manual index candidate
    index_res = await client.post(
        "/api/v1/semantic/index",
        json={"candidate_id": "api_search_01"}
    )
    assert index_res.status_code == 200
    index_data = index_res.json()
    assert index_data["success"] is True
    assert index_data["data"]["status"] == "success"

    # 7. Get vector store statistics
    stats_res = await client.get("/api/v1/semantic/statistics")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["success"] is True
    assert "summary" in stats_data["data"]

    # Clean up index files
    for col in ["summary", "career", "projects", "skills", "education"]:
        await provider.clear_collection(col)
