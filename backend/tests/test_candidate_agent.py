import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.candidate import (
    CandidateProfile, PersonalInfo, ExperienceDetail, ProjectDetail,
    EducationDetail, SkillDetail, CertificationDetail, BehaviorSignals,
    EngineeredFeatures, CandidateMetadata
)
from app.database.repositories.candidate import CandidateRepository
from app.services.agents.candidate_agent import candidate_agent
from app.services.agents.orchestrator import orchestrator
from app.services.candidate_analyzers.career_analyzer import career_analyzer
from app.services.candidate_analyzers.technical_analyzer import technical_analyzer
from app.services.candidate_analyzers.project_analyzer import project_analyzer
from app.services.candidate_analyzers.leadership_analyzer import leadership_analyzer
from app.services.candidate_analyzers.domain_analyzer import domain_analyzer
from app.services.candidate_analyzers.specialization_engine import specialization_engine
from app.services.candidate_analyzers.candidate_graph import candidate_graph_builder

async def seed_test_candidate(session: AsyncSession) -> str:
    profile = CandidateProfile(
        id="test_cand_99",
        personal_info=PersonalInfo(
            first_name="Alice",
            last_name="Coder",
            email="alice@coder.com",
            phone="1234567890",
            location="Berlin, Germany"
        ),
        experiences=[
            ExperienceDetail(
                company_name="TechCorp",
                job_title="Junior Python Engineer",
                start_date="2020-01-01",
                end_date="2022-01-01",
                description="Developing REST APIs with Python and Flask.",
                is_current=False
            ),
            ExperienceDetail(
                company_name="MegaScale",
                job_title="Senior Backend Architect",
                start_date="2022-01-01",
                end_date="present",
                description="Architected distributed microservices on AWS with FastAPI and Kubernetes. Mentored 5 junior engineers and made architectural decisions.",
                is_current=True
            )
        ],
        projects=[
            ProjectDetail(
                name="Payment Gateway Integration",
                description="High throughput credit card processing module for FinTech core.",
                technologies=["Python", "AWS", "FastAPI", "PostgreSQL", "Docker"],
                domain="FinTech",
                responsibilities=["Led the payments team", "Designed db schema", "Set up deployment pipeline in Jenkins"],
                duration_months=12
            )
        ],
        educations=[
            EducationDetail(
                institution="TU Berlin",
                degree="Master of Science",
                field_of_study="Computer Science",
                start_date="2018-09-01",
                end_date="2020-06-01"
            )
        ],
        skills=[
            SkillDetail(name="Python", normalized_name="Python", category="Programming Language", hierarchy_path=["Programming Language", "Backend"]),
            SkillDetail(name="AWS", normalized_name="AWS", category="Cloud Platform", hierarchy_path=["Cloud Platform"]),
            SkillDetail(name="FastAPI", normalized_name="FastAPI", category="Framework", hierarchy_path=["Framework", "Backend"])
        ],
        certifications=[
            CertificationDetail(
                name="AWS Certified Solutions Architect",
                issuing_organization="Amazon",
                issue_date="2022-05-01"
            )
        ],
        behavior_signals=BehaviorSignals(
            working_style="High Ownership",
            leadership_exposure=True,
            average_tenure_years=2.2,
            career_stability_score=85.0
        ),
        engineered_features=EngineeredFeatures(
            years_experience=4.5,
            distinct_companies=2,
            average_tenure=2.2,
            career_stability=85.0,
            project_count=1,
            certification_count=1,
            education_level="Master",
            technology_diversity=5,
            domain_diversity=1,
            leadership_score=4,
            cloud_score=3,
            ai_score=0,
            blockchain_score=0,
            cybersecurity_score=1
        ),
        metadata=CandidateMetadata(
            file_hash="mock_hash_123",
            version=1,
            raw_payload_checksum="mock_checksum_456"
        )
    )
    repo = CandidateRepository(session)
    await repo.upsert_candidate_profile(profile)
    await session.commit()
    return profile.id

@pytest.mark.anyio
async def test_career_analyzer():
    # Setup mock Pydantic profile
    profile = CandidateProfile(
        id="test_cand_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        experiences=[
            ExperienceDetail(company_name="Infosys", job_title="Developer", start_date="2020-01-01", end_date="2021-01-01"),
            ExperienceDetail(company_name="Google", job_title="Senior Lead Developer", start_date="2021-01-01", end_date="2023-01-01")
        ],
        projects=[ProjectDetail(name="P", domain="FinTech", technologies=["Python"])],
        engineered_features=EngineeredFeatures(years_experience=3.0, average_tenure=1.5, career_stability=70.0)
    )
    res = career_analyzer.analyze(profile)
    assert res["career_progression"]["total_years_experience"] == 3.0
    assert res["career_progression"]["promotions_count"] >= 1
    assert res["work_environment"]["consulting_vs_product"] == "Hybrid (Product & Consulting)"
    assert res["work_environment"]["startup_vs_enterprise"] == "Enterprise"

@pytest.mark.anyio
async def test_technical_analyzer():
    profile = CandidateProfile(
        id="test_cand_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        experiences=[
            ExperienceDetail(company_name="C", job_title="Python Developer", start_date="2020-01-01", end_date="2023-01-01", description="Working with Python.")
        ],
        projects=[ProjectDetail(name="P", technologies=["Python", "React"], duration_months=12)],
        skills=[SkillDetail(name="Python")]
    )
    res = technical_analyzer.analyze(profile)
    python_data = res["all_tech_details"]["Python"]
    assert python_data["years_of_usage"] >= 3.0
    assert python_data["proficiency_level"] in ["Advanced", "Expert"]
    assert "programming_languages" in res
    assert len(res["programming_languages"]) > 0

@pytest.mark.anyio
async def test_project_analyzer():
    profile = CandidateProfile(
        id="test_cand_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        projects=[
            ProjectDetail(
                name="Gateway API",
                description="Designed high throughput real-time payments API using microservices with Kubernetes, AWS, FastAPI to optimize low latency.",
                technologies=["FastAPI", "AWS", "Kubernetes", "Docker"],
                domain="FinTech",
                responsibilities=["Spearheaded architecture implementation", "Reduced page latency by 40%"],
                duration_months=18
            )
        ]
    )
    res = project_analyzer.analyze(profile)
    proj = res["projects"][0]
    assert proj["project_name"] == "Gateway API"
    assert proj["complexity"] == "High"
    assert proj["scale"] == "Medium"
    assert proj["ownership"] == "Lead / Owner"
    assert proj["project_score"] >= 80.0
    assert proj["has_impact"] is True
    assert proj["ai_experience"] is False

@pytest.mark.anyio
async def test_leadership_analyzer():
    profile = CandidateProfile(
        id="test_cand_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        experiences=[
            ExperienceDetail(company_name="C", job_title="Lead Developer", start_date="2020-01-01", end_date="2023-01-01", description="Mentored 3 junior devs. Architected distributed billing systems.")
        ],
        projects=[]
    )
    res = leadership_analyzer.analyze(profile)
    assert res["team_leadership"]["has_exposure"] is True
    assert res["mentoring"]["has_exposure"] is True
    assert res["architecture_ownership"]["has_exposure"] is True
    assert res["overall_leadership_score"] > 30.0

@pytest.mark.anyio
async def test_domain_analyzer():
    profile = CandidateProfile(
        id="test_cand_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        projects=[ProjectDetail(name="P", domain="FinTech", technologies=["Solidity"], description="Solidity smart contracts for banking ledger.")]
    )
    res = domain_analyzer.analyze(profile)
    assert "FinTech" in res["detected_domains"]
    assert "Blockchain" in res["detected_domains"]
    assert res["detected_domains"]["FinTech"]["exposure_years"] > 0.0

@pytest.mark.anyio
async def test_specialization_engine():
    profile = CandidateProfile(
        id="test_cand_99",
        personal_info=PersonalInfo(first_name="A", last_name="B"),
        experiences=[ExperienceDetail(company_name="C", job_title="Engineering Manager", start_date="2020-01-01", end_date="2023-01-01")],
        skills=[SkillDetail(name="FastAPI"), SkillDetail(name="Python")],
        projects=[ProjectDetail(name="P", technologies=["Kubernetes", "Docker"])]
    )
    res = specialization_engine.analyze(profile)
    assert "Backend Engineer" in res["specializations"]
    assert "Engineering Manager" in res["specializations"]

@pytest.mark.anyio
async def test_candidate_graph_builder():
    profile = CandidateProfile(
        id="test_cand_99",
        personal_info=PersonalInfo(first_name="Alice", last_name="Coder"),
        experiences=[ExperienceDetail(company_name="TechCorp", job_title="Architect")],
        projects=[ProjectDetail(name="Billing System", technologies=["Python"])]
    )
    kg = candidate_graph_builder.build_graph(profile, {
        "domains": {"detected_domains": {"FinTech": {"proficiency_level": "Expert", "exposure_years": 2.0}}},
        "leadership": {"team_leadership": {"has_exposure": True}}
    })
    nodes = {n["id"]: n for n in kg["nodes"]}
    edges = [(e["source"], e["target"], e["type"]) for e in kg["edges"]]

    assert "test_cand_99" in nodes
    assert nodes["test_cand_99"]["type"] == "Candidate"
    assert "comp_TechCorp" in nodes
    assert any(ed[0] == "test_cand_99" and ed[2] == "HAS_EXPERIENCE" for ed in edges)

@pytest.mark.anyio
async def test_candidate_agent_execution(db_session: AsyncSession):
    # Seed the DB
    candidate_id = await seed_test_candidate(db_session)
    
    await candidate_agent.initialize()
    context = {"db": db_session, "candidate_id": candidate_id}

    # Execute agent pipeline via orchestrator
    final_output, updated_context, trace = await orchestrator.execute_pipeline(
        pipeline=["candidate_intelligence"],
        initial_input=candidate_id,
        context=context
    )

    assert final_output["candidate_id"] == candidate_id
    assert "professional_summary" in final_output
    assert len(final_output["trace"]) > 0
    assert "Python Expert" in final_output["confidence_scores"]
    assert final_output["confidence_scores"]["Python Expert"] > 0.80
