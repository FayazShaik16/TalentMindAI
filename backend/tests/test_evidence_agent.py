import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.candidate import CandidateProfile
from app.services.agents.evidence_agent import evidence_verification_agent
from app.services.agents.orchestrator import orchestrator
from tests.test_candidate_agent import seed_test_candidate

# Import sub-engines
from app.services.evidence_analyzers.skill_evidence import skill_evidence_engine
from app.services.evidence_analyzers.timeline_engine import timeline_engine
from app.services.evidence_analyzers.project_evidence import project_evidence_analyzer
from app.services.evidence_analyzers.potential_engine import potential_engine
from app.services.evidence_analyzers.risk_detector import risk_detector
from app.services.evidence_analyzers.evidence_graph import evidence_graph_builder

@pytest.mark.anyio
async def test_skill_evidence_engine():
    # Setup simple mock Candidate profile
    from app.schemas.candidate import PersonalInfo, ExperienceDetail, ProjectDetail, SkillDetail
    profile = CandidateProfile(
        id="test_cand_ev_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        experiences=[
            ExperienceDetail(company_name="Mega", job_title="Engineer", start_date="2020-01-01", end_date="2022-01-01", description="Working with Java.")
        ],
        projects=[ProjectDetail(name="P1", technologies=["Java"], duration_months=12)],
        skills=[SkillDetail(name="Java")]
    )
    res = skill_evidence_engine.verify_skills(profile)
    assert "Java" in res
    assert res["Java"]["status"] in ["Verified", "Likely"]
    assert res["Java"]["evidence_score"] > 60.0

@pytest.mark.anyio
async def test_timeline_engine():
    from app.schemas.candidate import PersonalInfo, ExperienceDetail, ProjectDetail
    profile = CandidateProfile(
        id="test_cand_ev_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        experiences=[
            ExperienceDetail(company_name="C1", job_title="Developer", start_date="2019-01-01", end_date="2020-12-01", description="Python development")
        ],
        projects=[ProjectDetail(name="P", technologies=["Kubernetes"], duration_months=12)]
    )
    timeline = timeline_engine.generate_timeline(profile)
    assert 2019 in timeline
    assert "Python" in timeline[2019]

@pytest.mark.anyio
async def test_risk_detector():
    from app.schemas.candidate import PersonalInfo, ExperienceDetail, ProjectDetail, SkillDetail, EngineeredFeatures
    profile = CandidateProfile(
        id="test_cand_ev_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        experiences=[
            # Hopper warning: tenure is short
            ExperienceDetail(company_name="A1", job_title="Dev", start_date="2020-01-01", end_date="2020-08-01"),
            ExperienceDetail(company_name="A2", job_title="Dev", start_date="2020-09-01", end_date="2021-04-01"),
            ExperienceDetail(company_name="A3", job_title="Dev", start_date="2021-05-01", end_date="2021-12-01")
        ],
        projects=[],
        skills=[SkillDetail(name="Python")],
        engineered_features=EngineeredFeatures(average_tenure=0.7, distinct_companies=3, years_experience=2.0)
    )
    skills_verification = {"Python": {"status": "Verified", "duration_years": 2.0, "project_count": 0}}
    risks = risk_detector.detect_risks(profile, skills_verification)
    assert risks["risk_level"] in ["Medium", "High"]
    assert any("hopping" in exp.lower() for exp in risks["explanations"])

@pytest.mark.anyio
async def test_evidence_verification_agent(db_session: AsyncSession):
    candidate_id = await seed_test_candidate(db_session)
    await evidence_verification_agent.initialize()

    context = {"db": db_session, "candidate_id": candidate_id}
    res = await orchestrator.execute_pipeline(
        pipeline=["evidence_verification"],
        initial_input=candidate_id,
        context=context
    )

    final_output = res[0]
    assert final_output["candidate_id"] == candidate_id
    assert "skill_verification" in final_output
    assert "timeline" in final_output
    assert "potential_metrics" in final_output
    assert "risk_analysis" in final_output
    assert "evidence_graph" in final_output
    assert "overall_verification_confidence" in final_output["confidence_scores"]
