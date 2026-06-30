import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.search_engine import search_engine
from app.providers.vector.faiss import FAISSProvider
from app.database.models.candidate import Candidate
from app.database.repositories.candidate import CandidateRepository
from app.api.v1.routers.semantic import index_candidate_profile
from tests.test_pipeline import clear_db

@pytest.mark.asyncio
async def test_search_engine_and_trace(db_session: AsyncSession):
    """
    Integrates the search engine with the database, checks similarity lookup,
    metadata filtering, and AI search trace generation.
    """
    await clear_db(db_session)
    
    # 1. Add mock candidate record in database
    from app.schemas.candidate import CandidateProfile, PersonalInfo, SkillDetail, EngineeredFeatures
    
    profile = CandidateProfile(
        id="cand_search_01",
        personal_info=PersonalInfo(
            first_name="Sam",
            last_name="Python",
            email="sam@example.com",
            phone="+9999",
            location="Chicago"
        ),
        experiences=[],
        projects=[],
        educations=[],
        skills=[
            SkillDetail(name="Python", normalized_name="Python", category="Programming Language"),
            SkillDetail(name="FastAPI", normalized_name="FastAPI", category="Backend Framework")
        ],
        engineered_features=EngineeredFeatures(
            years_experience=3.0,
            education_level="Bachelor"
        )
    )
    
    repo = CandidateRepository(db_session)
    await repo.upsert_candidate_profile(profile)
    await db_session.commit()
    
    # Reload from DB to get Candidate model instance
    db_cand = await repo.get_candidate_profile("cand_search_01")
    assert db_cand is not None
    
    # 2. Build index for candidate
    provider = FAISSProvider()
    # Ensure test directories are clean
    await provider.clear_collection("summary")
    
    # Index the candidate profile
    await index_candidate_profile(db_cand, db_session, provider)
    
    # 3. Perform semantic search
    res = await search_engine.search(
        query="Python developer with FastAPI experience in Chicago",
        collection_name="summary",
        limit=5
    )
    
    assert "results" in res
    assert "trace" in res
    assert len(res["results"]) == 1
    assert res["results"][0]["candidate_id"] == "cand_search_01"
    
    # Check trace
    trace = res["trace"]
    assert trace["recruiter_query"] == "Python developer with FastAPI experience in Chicago"
    assert "timing_logs" in trace
    assert len(trace["execution_steps"]) > 0
    assert "embedding_generation_sec" in trace["timing_logs"]
    
    # 4. Perform search with mismatch filter -> should yield 0 results
    res_mismatch = await search_engine.search(
        query="Python developer",
        collection_name="summary",
        limit=5,
        filter_metadata={"location": "Boston"}  # Sam is in Chicago
    )
    assert len(res_mismatch["results"]) == 0
    
    # 5. Perform search with matching filter -> should yield 1 result
    res_match = await search_engine.search(
        query="Python developer",
        collection_name="summary",
        limit=5,
        filter_metadata={"location": "Chicago"}
    )
    assert len(res_match["results"]) == 1
    
    # Clean up FAISS index
    await provider.clear_collection("summary")
