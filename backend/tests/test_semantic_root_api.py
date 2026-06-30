import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.candidate import Candidate
from app.database.repositories.candidate import CandidateRepository
from app.schemas.candidate import CandidateProfile, PersonalInfo
from tests.test_pipeline import clear_db
from app.providers.vector.faiss import FAISSProvider

@pytest.mark.asyncio
async def test_semantic_root_endpoints(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies that the root-level endpoints /embeddings/build, /semantic/search,
    and /semantic/status function correctly.
    """
    await clear_db(db_session)
    provider = FAISSProvider()
    for col in ["summary", "career", "projects", "skills", "education"]:
        await provider.clear_collection(col)

    # 1. Insert a mock candidate into DB
    profile = CandidateProfile(
        id="root_api_search_01",
        personal_info=PersonalInfo(
            first_name="Jane",
            last_name="RootSearcher",
            email="jane.root@example.com",
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

    # 2. Check root status endpoint
    status_res = await client.get("/semantic/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["success"] is True
    assert status_data["data"]["active_model"] == "BAAI/bge-base-en-v1.5"

    # 3. Build embeddings via root build endpoint
    build_res = await client.post("/embeddings/build")
    assert build_res.status_code == 200
    build_data = build_res.json()
    assert build_data["success"] is True
    assert build_data["data"]["processed_count"] == 1

    # 4. Search via root search endpoint
    search_payload = {
        "query": "Looking for Jane RootSearcher in Boston",
        "collection": "summary",
        "limit": 5,
        "filter_metadata": {"location": "Boston"}
    }
    search_res = await client.post("/semantic/search", json=search_payload)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["success"] is True
    assert len(search_data["data"]["results"]) == 1
    assert search_data["data"]["results"][0]["candidate_id"] == "root_api_search_01"

    # Clean up index files
    for col in ["summary", "career", "projects", "skills", "education"]:
        await provider.clear_collection(col)
