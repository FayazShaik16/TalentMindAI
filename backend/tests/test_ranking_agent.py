import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repositories.job import JobRepository
from app.database.repositories.ranking import RankingRepository
from app.database.models.job import JobDescription
from tests.test_candidate_agent import seed_test_candidate
from app.services.agents.job_agent import job_agent
from app.services.agents.candidate_agent import candidate_agent
from app.services.agents.evidence_agent import evidence_verification_agent
from app.services.agents.ranking_agent import ranking_agent
from app.services.agents.orchestrator import orchestrator
from app.services.matching.matching_engine import MultiFactorScoringEngine

async def seed_test_job_and_candidate(session: AsyncSession) -> tuple[str, str]:
    # 1. Seed candidate
    cand_id = await seed_test_candidate(session)
    
    # Initialize agents
    await job_agent.initialize()
    await candidate_agent.initialize()
    await evidence_verification_agent.initialize()
    await ranking_agent.initialize()

    # Ingest candidate intelligence and evidence
    context_cand = {"db": session, "candidate_id": cand_id}
    await orchestrator.execute_pipeline(
        pipeline=["candidate_intelligence", "evidence_verification"],
        initial_input=cand_id,
        context=context_cand
    )

    # 2. Seed Job
    job_repo = JobRepository(session)
    existing_job = await job_repo.get_by_id("test_job_99")
    if not existing_job:
        from tests.test_job_agent import SAMPLE_JD
        context_job = {"db": session, "job_id": "test_job_99"}
        job_res = await job_agent.execute(SAMPLE_JD, context_job)
        
        # Create database model
        job_model = JobDescription(
            id="test_job_99",
            raw_text=SAMPLE_JD,
            title=job_res["title"],
            department=job_res["department"],
            seniority=job_res["seniority"],
            experience_required=job_res["experience_required"],
            employment_type=job_res["employment_type"],
            remote_type=job_res["remote_type"],
            intent_profile=job_res["intent_profile"],
            intent_graph=job_res["intent_graph"],
            trace=job_res["trace"],
            confidence_scores=job_res["confidence_scores"]
        )
        await job_repo.create(job_model)
        await session.flush()
    
    return "test_job_99", cand_id

@pytest.mark.anyio
async def test_ranking_agent_execution(db_session: AsyncSession):
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    
    context = {
        "db": db_session,
        "candidate_ids": [cand_id],
        "top_k_rerank": 0  # Skip rerank for simple unit test speed
    }

    res = await orchestrator.execute_pipeline(
        pipeline=["hybrid_ranking"],
        initial_input=job_id,
        context=context
    )

    final_output = res[0]
    assert final_output["job_id"] == job_id
    assert len(final_output["rankings"]) == 1
    
    rank_item = final_output["rankings"][0]
    assert rank_item["candidate_id"] == cand_id
    assert rank_item["overall_score"] > 0.0
    assert rank_item["rank"] == 1
    assert "recommendation" in rank_item
    assert "scoring_dimensions" in rank_item
    assert len(final_output["trace"]) > 0
    assert "ranking_latency_sec" in final_output["statistics"]

@pytest.mark.anyio
async def test_multi_factor_scoring_dimensions(db_session: AsyncSession):
    # Retrieve scoring engine
    engine = MultiFactorScoringEngine()
    
    # Define simple dummy data for matching dimension unit tests
    job_profile = {"skills": {"primary_skills": ["Python", "AWS"]}}
    from app.schemas.candidate import CandidateProfile, PersonalInfo, SkillDetail
    profile = CandidateProfile(
        id="test_cand_t1",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        experiences=[],
        projects=[],
        skills=[SkillDetail(name="Python")]
    )
    
    res = engine.compute_skill_match(job_profile, profile, None, 0.10)
    assert res["raw_score"] > 0.0
    assert "Coverage" in res["explanation"]
    assert res["weight"] == 0.10
