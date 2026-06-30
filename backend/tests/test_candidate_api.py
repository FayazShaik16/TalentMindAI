import pytest
from httpx import AsyncClient
from app.schemas.candidate import (
    CandidateProfile, PersonalInfo, ExperienceDetail, ProjectDetail,
    EducationDetail, SkillDetail, CertificationDetail, BehaviorSignals,
    EngineeredFeatures, CandidateMetadata
)
from app.database.repositories.candidate import CandidateRepository

async def seed_api_candidate(client: AsyncClient, db_session) -> str:
    profile = CandidateProfile(
        id="api_test_cand_1",
        personal_info=PersonalInfo(
            first_name="Dev",
            last_name="Architect",
            email="dev@arch.com",
            phone="+919876543210",
            location="Mumbai, India"
        ),
        experiences=[
            ExperienceDetail(
                company_name="TCS",
                job_title="System Analyst",
                start_date="2018-05-01",
                end_date="2021-05-01",
                description="Developing enterprise services with Python.",
                is_current=False
            ),
            ExperienceDetail(
                company_name="Flipkart",
                job_title="Lead Architect",
                start_date="2021-05-01",
                end_date="present",
                description="Designed high scale distribution systems. Mentored engineers.",
                is_current=True
            )
        ],
        projects=[
            ProjectDetail(
                name="Inventory Tracker",
                description="Microservices inventory management system on GCP.",
                technologies=["Go", "GCP", "Kubernetes", "Redis"],
                domain="E-commerce",
                responsibilities=["Led backend design", "Optimized DB lookups"],
                duration_months=24
            )
        ],
        educations=[
            EducationDetail(
                institution="IIT Bombay",
                degree="B.Tech",
                field_of_study="Electrical",
                start_date="2014-07-01",
                end_date="2018-05-01"
            )
        ],
        skills=[
            SkillDetail(name="Python"),
            SkillDetail(name="Go"),
            SkillDetail(name="GCP"),
            SkillDetail(name="Kubernetes")
        ],
        certifications=[],
        behavior_signals=BehaviorSignals(
            working_style="High Ownership",
            leadership_exposure=True,
            average_tenure_years=3.0,
            career_stability_score=90.0
        ),
        engineered_features=EngineeredFeatures(
            years_experience=6.0,
            distinct_companies=2,
            average_tenure=3.0,
            career_stability=90.0,
            project_count=1,
            certification_count=0,
            education_level="Bachelor",
            technology_diversity=4,
            domain_diversity=1,
            leadership_score=4,
            cloud_score=2,
            ai_score=0,
            blockchain_score=0,
            cybersecurity_score=0
        ),
        metadata=CandidateMetadata(
            file_hash="api_hash_1",
            version=1
        )
    )
    repo = CandidateRepository(db_session)
    await repo.upsert_candidate_profile(profile)
    await db_session.commit()
    return profile.id

@pytest.mark.anyio
async def test_candidate_api_flow(client: AsyncClient, db_session):
    # 1. Seed Candidate in test SQLite
    cand_id = await seed_api_candidate(client, db_session)

    # 2. Test POST /candidate/analyze
    analyze_res = await client.post("/candidate/analyze", json={"candidate_id": cand_id})
    assert analyze_res.status_code == 200
    analyze_data = analyze_res.json()
    assert analyze_data["success"] is True
    assert analyze_data["data"]["candidate_id"] == cand_id
    assert analyze_data["data"]["professional_summary"] != ""
    assert "Backend Engineer" in analyze_data["data"]["specializations"]

    # 3. Test GET /candidate/{id}/intelligence
    intel_res = await client.get(f"/candidate/{cand_id}/intelligence")
    assert intel_res.status_code == 200
    intel_data = intel_res.json()
    assert intel_data["success"] is True
    assert intel_data["data"]["candidate_id"] == cand_id
    assert "career_intelligence" in intel_data["data"]

    # 4. Test GET /candidate/{id}/knowledge-graph
    kg_res = await client.get(f"/candidate/{cand_id}/knowledge-graph")
    assert kg_res.status_code == 200
    kg_data = kg_res.json()
    assert kg_data["success"] is True
    assert "nodes" in kg_data["data"]
    assert "edges" in kg_data["data"]

    # 5. Test GET /candidate/{id}/career-analysis
    career_res = await client.get(f"/candidate/{cand_id}/career-analysis")
    assert career_res.status_code == 200
    career_data = career_res.json()
    assert career_data["success"] is True
    assert "career_intelligence" in career_data["data"]
    assert "career_growth" in career_data["data"]

    # 6. Test GET /candidate/{id}/technical-analysis
    tech_res = await client.get(f"/candidate/{cand_id}/technical-analysis")
    assert tech_res.status_code == 200
    tech_data = tech_res.json()
    assert tech_data["success"] is True
    assert "all_tech_details" in tech_data["data"]

    # 7. Test GET /candidate/{id}/leadership-analysis
    lead_res = await client.get(f"/candidate/{cand_id}/leadership-analysis")
    assert lead_res.status_code == 200
    lead_data = lead_res.json()
    assert lead_data["success"] is True
    assert "team_leadership" in lead_data["data"]

    # 8. Test GET /candidate/{id}/projects-analysis
    proj_res = await client.get(f"/candidate/{cand_id}/projects-analysis")
    assert proj_res.status_code == 200
    proj_data = proj_res.json()
    assert proj_data["success"] is True
    assert "projects" in proj_data["data"]
    assert len(proj_data["data"]["projects"]) > 0

    # 9. Test GET /candidate/{id}/domains
    dom_res = await client.get(f"/candidate/{cand_id}/domains")
    assert dom_res.status_code == 200
    dom_data = dom_res.json()
    assert dom_data["success"] is True
    assert "detected_domains" in dom_data["data"]

    # 10. Test GET /candidate/{id}/trace
    trace_res = await client.get(f"/candidate/{cand_id}/trace")
    assert trace_res.status_code == 200
    trace_data = trace_res.json()
    assert trace_data["success"] is True
    assert len(trace_data["data"]) > 0

@pytest.mark.anyio
async def test_get_candidate_intelligence_not_found(client: AsyncClient):
    get_res = await client.get("/candidate/nonexistent_cand_id/intelligence")
    assert get_res.status_code == 404
    get_data = get_res.json()
    assert get_data["success"] is False
    assert "not found" in get_data["error"]["message"].lower()
