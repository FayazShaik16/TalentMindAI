import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.candidate import (
    CandidateProfile, PersonalInfo, SkillDetail, EngineeredFeatures
)
from app.services.explainability.analyzers import (
    StrengthAnalyzer, WeaknessAnalyzer, TransferableSkillsFinder,
    MissingSkillsEngine, InterviewRecommendationEngine, HiringNarrativeGenerator
)
from app.services.explainability.comparison import (
    CandidateComparisonEngine, DecisionIntelligenceEngine
)
from app.services.agents.explainability_agent import explainability_agent
from app.services.agents.orchestrator import orchestrator
from tests.test_ranking_agent import seed_test_job_and_candidate

@pytest.mark.anyio
async def test_strength_analyzer():
    analyzer = StrengthAnalyzer()
    
    # Mock profile and ranking item
    profile = CandidateProfile(
        id="test_cand_t1",
        personal_info=PersonalInfo(first_name="Alice", last_name="Coder"),
        experiences=[],
        projects=[],
        skills=[SkillDetail(name="Python")],
        engineered_features=EngineeredFeatures(
            years_experience=5.0,
            distinct_companies=1,
            average_tenure=5.0,
            career_stability=100.0,
            project_count=0,
            certification_count=0,
            education_level="Bachelor",
            technology_diversity=1,
            domain_diversity=0,
            leadership_score=0,
            cloud_score=0,
            ai_score=0,
            blockchain_score=0,
            cybersecurity_score=0
        )
    )
    
    # We will pass dummy intelligence/evidence or None and a ranking item
    ranking_item = {
        "candidate_id": "test_cand_t1",
        "overall_score": 85.0,
        "hiring_confidence": 0.9,
        "recommendation": "Hire",
        "scoring_dimensions": {}
    }
    
    # If intelligence is None, strengths still shouldn't crash
    strengths = analyzer.analyze(profile, None, None, ranking_item)
    assert isinstance(strengths, list)

@pytest.mark.anyio
async def test_weakness_analyzer():
    analyzer = WeaknessAnalyzer()
    profile = CandidateProfile(
        id="test_cand_t1",
        personal_info=PersonalInfo(first_name="Alice", last_name="Coder"),
        experiences=[],
        projects=[],
        skills=[SkillDetail(name="Python")],
        engineered_features=EngineeredFeatures(
            years_experience=2.0,  # Below mid-senior level
            distinct_companies=1,
            average_tenure=2.0,
            career_stability=80.0,
            project_count=0,
            certification_count=0,
            education_level="Bachelor",
            technology_diversity=1,
            domain_diversity=0,
            leadership_score=0,
            cloud_score=0,
            ai_score=0,
            blockchain_score=0,
            cybersecurity_score=0
        )
    )
    ranking_item = {
        "candidate_id": "test_cand_t1",
        "overall_score": 55.0,
        "hiring_confidence": 0.5,
        "recommendation": "Interview",
        "missing_skills": ["Kubernetes", "FastAPI"],
        "scoring_dimensions": {}
    }
    
    weaknesses = analyzer.analyze(profile, None, None, ranking_item)
    assert len(weaknesses) >= 2
    # Verify experience gap and missing technical gaps are identified
    cats = [w["category"] for w in weaknesses]
    assert "Technical" in cats
    assert "Experience" in cats

@pytest.mark.anyio
async def test_transferable_skills():
    finder = TransferableSkillsFinder()
    missing = ["FastAPI", "Kubernetes", "PyTorch"]
    cand_skills = ["Flask", "Docker Swarm", "Tensorflow"]
    
    transferable = finder.find(missing, cand_skills)
    assert len(transferable) == 3
    assert transferable[0]["missing_skill"] == "FastAPI"
    assert transferable[0]["transferable_skill"] == "Flask"

@pytest.mark.anyio
async def test_missing_skills_engine():
    engine = MissingSkillsEngine()
    missing = ["FastAPI", "Kubernetes", "C++"]
    transferable = [
        {"missing_skill": "FastAPI", "transferable_skill": "Flask", "explanation": "Flask is transferable to FastAPI"}
    ]
    
    categorized = engine.analyze(missing, transferable)
    assert len(categorized["important_missing"]) == 1
    assert categorized["important_missing"][0]["name"] == "FastAPI"
    assert categorized["important_missing"][0]["learning_effort"] == "Low (1-2 weeks)"
    assert len(categorized["critical_missing"]) > 0

@pytest.mark.anyio
async def test_interview_recommendation_engine():
    engine = InterviewRecommendationEngine()
    ranking_item = {
        "candidate_id": "c1",
        "recommendation": "Hire",
        "scoring_dimensions": {
            "leadership": {"raw_score": 75.0},
            "risk": {"raw_score": 90.0}
        }
    }
    strengths = [{"name": "Auth expert", "category": "Technical"}]
    weaknesses = []
    
    plan = engine.generate(ranking_item, strengths, weaknesses)
    assert plan["overall_recommendation"] == "Hire"
    assert len(plan["interview_focus_areas"]) > 0

@pytest.mark.anyio
async def test_hiring_narrative_generator():
    generator = HiringNarrativeGenerator()
    profile = CandidateProfile(
        id="t1",
        personal_info=PersonalInfo(first_name="John", last_name="Doe"),
        experiences=[],
        projects=[],
        skills=[],
        engineered_features=EngineeredFeatures(
            years_experience=6.5,
            distinct_companies=2,
            average_tenure=3.25,
            career_stability=90.0,
            project_count=1,
            certification_count=0,
            education_level="Bachelor",
            technology_diversity=5,
            domain_diversity=1,
            leadership_score=2,
            cloud_score=2,
            ai_score=0,
            blockchain_score=0,
            cybersecurity_score=0
        )
    )
    ranking_item = {
        "overall_score": 88.5,
        "hiring_confidence": 0.95,
        "recommendation": "Strong Hire"
    }
    strengths = [{"name": "Backend Python", "category": "Technical", "impact": "High"}]
    weaknesses = []
    
    narrative = generator.generate(profile, ranking_item, strengths, weaknesses)
    assert "John Doe" in narrative
    assert "Strong Hire" in narrative
    assert "6.5" in narrative

@pytest.mark.anyio
async def test_comparison_and_decision_engines():
    comp_engine = CandidateComparisonEngine()
    di_engine = DecisionIntelligenceEngine()
    
    cand_a = {
        "candidate_id": "cand_a",
        "personal_info": {"first_name": "Alice", "last_name": "Smith"},
        "overall_score": 90.0,
        "hiring_confidence": 0.95,
        "recommendation": "Strong Hire",
        "strengths": [{"name": "AWS Architecture"}],
        "weaknesses": [],
        "missing_skills": {"critical_missing": [], "important_missing": []},
        "match_breakdown": {
            "semantic": {"normalized_score": 92.0},
            "skills": {"normalized_score": 95.0},
            "career": {"normalized_score": 90.0},
            "leadership": {"normalized_score": 85.0},
            "potential": {"normalized_score": 90.0},
            "projects": {"normalized_score": 93.0},
            "risk": {"penalty_applied": 0.0}
        }
    }
    
    cand_b = {
        "candidate_id": "cand_b",
        "personal_info": {"first_name": "Bob", "last_name": "Jones"},
        "overall_score": 80.0,
        "hiring_confidence": 0.85,
        "recommendation": "Hire",
        "strengths": [{"name": "Python Coding"}],
        "weaknesses": [{"name": "Missing AWS Expertise"}],
        "missing_skills": {"critical_missing": [{"name": "AWS"}], "important_missing": []},
        "match_breakdown": {
            "semantic": {"normalized_score": 82.0},
            "skills": {"normalized_score": 75.0},
            "career": {"normalized_score": 85.0},
            "leadership": {"normalized_score": 70.0},
            "potential": {"normalized_score": 80.0},
            "projects": {"normalized_score": 80.0},
            "risk": {"penalty_applied": -5.0}
        }
    }
    
    # 1. Compare matrix
    comparison = comp_engine.compare([cand_a, cand_b])
    matrix = comparison["comparison_matrix"]
    assert "cand_a" in matrix
    assert "cand_b" in matrix
    assert matrix["cand_a"]["overall_score"] == 90.0
    
    # 2. Differentiators
    di = di_engine.generate_differentiators(cand_a, cand_b)
    assert di["primary_candidate"] == "cand_a"
    assert di["score_gap"] == 10.0
    assert len(di["differentiators"]) > 0

@pytest.mark.anyio
async def test_explainability_agent_pipeline(db_session: AsyncSession):
    job_id, cand_id = await seed_test_job_and_candidate(db_session)
    await db_session.commit()
    
    # Run hybrid ranking first so we have ranking records
    context = {
        "db": db_session,
        "candidate_ids": [cand_id],
        "top_k_rerank": 0
    }
    
    await explainability_agent.initialize()
    
    # Execute agent through the orchestrator
    result = await orchestrator.execute_pipeline(
        pipeline=["explainability"],
        initial_input=job_id,
        context=context
    )
    
    final_output = result[0]
    assert final_output["job_id"] == job_id
    assert len(final_output["explanations"]) == 1
    
    explanation_pkg = final_output["explanations"][0]
    assert explanation_pkg["candidate_id"] == cand_id
    assert explanation_pkg["match_percentage"] > 0.0
    assert len(explanation_pkg["strengths"]) > 0
